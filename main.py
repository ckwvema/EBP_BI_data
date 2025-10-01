#!/usr/bin/env python3
import requests
import pandas as pd
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional
import time
from functools import wraps

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function calls on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


class EBP:
    def __init__(self):
        """Initialize EBP client with environment variables."""
        self.username = os.getenv('EBP_USERNAME')
        self.password = os.getenv('EBP_PASSWORD')
        self.base_url = os.getenv('EBP_BASE_URL')
        self.default_limit = int(os.getenv('DEFAULT_LIMIT', '20000'))
        self.auth_header = None
        
        if not all([self.username, self.password, self.base_url]):
            raise ValueError("Missing required environment variables: EBP_USERNAME, EBP_PASSWORD, EBP_BASE_URL")
        
        logger.info("Initializing EBP client...")
        self.login()

    @retry_on_failure(max_retries=3, delay=2.0)
    def login(self) -> bool:
        """Authenticate with EBP API."""
        url = f"{self.base_url}/api/admin/v1/session/authenticate"
        credentials = {"username": self.username, "password": self.password}
        headers = {"Content-Type": "application/json"}

        try:
            logger.info("Attempting to authenticate with EBP API...")
            response = requests.post(url, json=credentials, headers=headers, verify=True, timeout=30)
            response.raise_for_status()
            
            token = response.json().get("token")
            if token:
                self.auth_header = {
                    "Authorization": f"Bearer {token}", 
                    "Content-Type": "application/json"
                }
                logger.info("Successfully authenticated with EBP API")
                return True
            else:
                logger.error("Token not found in authentication response")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=1.0)
    def fetch_data(self, endpoint: str, limit: Optional[int] = None) -> Optional[List[Dict]]:
        """Fetch data from EBP API endpoint."""
        if not self.auth_header:
            logger.error("Not authenticated. Please login first.")
            return None
            
        url = f"{self.base_url}{endpoint}"
        limit = limit or self.default_limit
        
        try:
            logger.info(f"Fetching data from {endpoint} (limit: {limit})")
            response = requests.get(
                url, 
                params={'limit': limit}, 
                headers=self.auth_header, 
                verify=True, 
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            logger.info(f"Successfully fetched {len(elements)} records from {endpoint}")
            return elements
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from {endpoint}: {e}")
            raise
        
    def get_managers(self, contracts_df: pd.DataFrame) -> pd.DataFrame:
        """Fetch manager data for all contracts."""
        if contracts_df.empty:
            logger.warning("No contracts provided for manager data fetching")
            return pd.DataFrame()
            
        managers = []
        total_contracts = len(contracts_df)
        logger.info(f"Fetching manager data for {total_contracts} contracts...")
        
        for idx, row in contracts_df.iterrows():
            try:
                if idx % 100 == 0:  # Progress logging every 100 contracts
                    logger.info(f"Processing contract {idx + 1}/{total_contracts}")
                
                response = requests.get(
                    f"{self.base_url}/api/admin/v1/contracts/{row['contractId']}/managers",
                    params={'limit': self.default_limit},
                    headers=self.auth_header,
                    verify=True,
                    timeout=30
                )
                
                if response.status_code == 200:
                    manager_data = response.json()
                    if manager_data:  # Check if data exists
                        df = pd.DataFrame(manager_data)
                        
                        # Normalize nested JSON data
                        df = pd.concat([
                            pd.json_normalize(df['contact']),
                            pd.json_normalize(df['address']),
                            pd.json_normalize(df['personal']),
                            df.drop(columns=['contact', 'address', 'personal'])
                        ], axis=1)
                        
                        # Filter out specific email
                        df = df[~df['email'].isin(['zev@ckw.ch'])].reset_index(drop=True)
                        
                        # Clean and rename columns
                        df = df.rename(columns={'id': 'profileId'})
                        df = df.drop(columns=['profileId', 'isBlocked', 'party', 'externalUserId', 'externalUserParties', 'activeState'], errors='ignore')
                        
                        # Add contract information
                        df['contractId'] = row['contractId']
                        df['contractName'] = row['contractName']
                        df['contractActiveState'] = row['contractActiveState']
                        df['productName'] = row['productName']
                        df['areaName'] = row['areaName']
                        
                        managers.append(df)
                        
            except Exception as e:
                logger.warning(f"Failed to fetch managers for contract {row['contractId']}: {e}")
                continue
        
        if not managers:
            logger.warning("No manager data found")
            return pd.DataFrame()
            
        # Combine all manager data
        output = pd.concat(managers, ignore_index=True)
        
        # Select and order columns
        expected_columns = [
            'contractId', 'contractName', 'contractActiveState', 'productName', 'areaName',
            'salutation', 'firstName', 'lastName', 'userType', 'username', 'mobile', 
            'email', 'telephone', 'street', 'houseNumber', 'postalCode', 'city'
        ]
        
        # Only include columns that exist in the dataframe
        available_columns = [col for col in expected_columns if col in output.columns]
        output = output[available_columns]
        
        logger.info(f"Successfully processed {len(output)} manager records")
        return output


def safe_rename_columns(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """Safely rename columns, only renaming those that exist."""
    existing_columns = {old: new for old, new in column_mapping.items() if old in df.columns}
    if existing_columns:
        df = df.rename(columns=existing_columns)
        logger.debug(f"Renamed columns: {existing_columns}")
    return df


def safe_drop_columns(df: pd.DataFrame, columns_to_drop: List[str]) -> pd.DataFrame:
    """Safely drop columns, only dropping those that exist."""
    existing_columns = [col for col in columns_to_drop if col in df.columns]
    if existing_columns:
        df = df.drop(columns=existing_columns)
        logger.debug(f"Dropped columns: {existing_columns}")
    return df


def transform_buildings(df: pd.DataFrame) -> pd.DataFrame:
    """Transform buildings data."""
    logger.info(f"Transforming buildings data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty buildings dataframe provided")
        return df
    
    df = safe_rename_columns(df, {
        "id": "buildingId",
        "name": "buildingName",
        "activeState": "buildingActiveState"
    })
    
    logger.info(f"Buildings transformation completed: {len(df)} records")
    return df


def transform_utility_units(df: pd.DataFrame) -> pd.DataFrame:
    """Transform utility units data."""
    logger.info(f"Transforming utility units data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty utility units dataframe provided")
        return df
    
    # Drop unnecessary columns
    df = safe_drop_columns(df, ["participations", "participationObjects"])
    
    # Rename columns
    df = safe_rename_columns(df, {
        "id": "utilityUnitId",
        "name": "utilityUnitName",
        "usageType": "utilityUnitUsageType",
        "activeState": "utilityUnitActiveState"
    })
    
    logger.info(f"Utility units transformation completed: {len(df)} records")
    return df


def transform_meters(df: pd.DataFrame) -> pd.DataFrame:
    """Transform meters data."""
    logger.info(f"Transforming meters data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty meters dataframe provided")
        return df
    
    # Rename columns
    df = safe_rename_columns(df, {
        "id": "meterId",
        "activeState": "meterActiveState"
    })
    
    # Handle date columns
    df['billableTo'] = df['billableTo'].fillna('2099-12-31')
    
    # Convert date columns with error handling
    for date_col in ['billableFrom', 'billableTo']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors='coerce')
            invalid_dates = df[date_col].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Found {invalid_dates} invalid dates in {date_col}")
    
    logger.info(f"Meters transformation completed: {len(df)} records")
    return df


def transform_contracts(df: pd.DataFrame) -> pd.DataFrame:
    """Transform contracts data."""
    logger.info(f"Transforming contracts data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty contracts dataframe provided")
        return df
    
    # Extract product name safely
    if 'product' in df.columns:
        df['productName'] = df['product'].apply(
            lambda x: x.get('name') if isinstance(x, dict) else None
        )
    else:
        logger.warning("Product column not found in contracts data")
        df['productName'] = None
    
    # Rename columns
    df = safe_rename_columns(df, {
        "id": "contractId",
        "name": "contractName",
        "activeState": "contractActiveState",
    })
    
    # Select required columns
    required_columns = [
        'contractId', 'contractName', 'contractActiveState', 'startDate', 'endDate', 
        'productId', 'productName', 'areaId', 'areaName', 'loadDate'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in required_columns if col in df.columns]
    df = df[available_columns]
    
    # Handle date columns
    df['endDate'] = df['endDate'].fillna('2099-12-31')
    
    for date_col in ['startDate', 'endDate']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors='coerce')
            invalid_dates = df[date_col].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Found {invalid_dates} invalid dates in {date_col}")
    
    logger.info(f"Contracts transformation completed: {len(df)} records")
    return df


def transform_areas(df: pd.DataFrame) -> pd.DataFrame:
    """Transform areas data."""
    logger.info(f"Transforming areas data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty areas dataframe provided")
        return df
    
    df = safe_rename_columns(df, {
        "id": "areaId",
        "name": "areaName",
    })
    
    logger.info(f"Areas transformation completed: {len(df)} records")
    return df


def transform_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Transform profiles data."""
    logger.info(f"Transforming profiles data: {len(df)} records")
    
    if df.empty:
        logger.warning("Empty profiles dataframe provided")
        return df
    
    df = safe_rename_columns(df, {
        "id": "profileId"
    })
    
    logger.info(f"Profiles transformation completed: {len(df)} records")
    return df


def apply_data_filters(df: pd.DataFrame, filter_words: List[str], column_name: str) -> pd.DataFrame:
    """Apply filtering based on filter words to a specific column."""
    if df.empty or column_name not in df.columns:
        logger.warning(f"Cannot apply filters: empty dataframe or column '{column_name}' not found")
        return df
    
    original_count = len(df)
    pattern = '|'.join(filter_words)
    mask = df[column_name].str.contains(pattern, case=False, na=False)
    filtered_df = df[~mask].reset_index(drop=True)
    filtered_count = len(filtered_df)
    removed_count = original_count - filtered_count
    
    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} records containing filter words from {column_name}")
    
    return filtered_df


def create_export_directories(base_path: str, subdirectories: List[str]) -> None:
    """Create export directories if they don't exist."""
    for subdir in subdirectories:
        dir_path = Path(base_path) / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created/verified directory: {dir_path}")


def export_dataframe_to_csv(df: pd.DataFrame, file_path: Path, table_name: str) -> bool:
    """Export dataframe to CSV with error handling."""
    try:
        if df.empty:
            logger.warning(f"No data to export for {table_name}")
            return False
            
        df.to_csv(file_path, index=False)
        logger.info(f"Successfully exported {table_name}: {len(df)} records to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export {table_name} to {file_path}: {e}")
        return False


def export_all_data(dataframes: Dict[str, pd.DataFrame]) -> None:
    """Export all dataframes to CSV files."""
    logger.info("Starting data export process...")
    
    try:
        # Get configuration from environment
        base_path = os.getenv('EXPORT_BASE_PATH')
        subdirectories = os.getenv('EXPORT_SUBDIRECTORIES', 'areas,contracts,buildings,utility_units,meters,managers,profiles').split(',')
        
        if not base_path:
            raise ValueError("EXPORT_BASE_PATH not set in environment variables")
        
        # Create export directories
        create_export_directories(base_path, subdirectories)
        
        # Generate timestamp for filenames
        today = datetime.today().strftime("%Y%m%d")
        
        # Export each dataframe
        export_results = {}
        for table_name, df in dataframes.items():
            if table_name in subdirectories:
                file_path = Path(base_path) / table_name / f'{today}_{table_name}.csv'
                success = export_dataframe_to_csv(df, file_path, table_name)
                export_results[table_name] = success
            else:
                logger.warning(f"Subdirectory '{table_name}' not configured for export")
        
        # Summary
        successful_exports = sum(export_results.values())
        total_exports = len(export_results)
        logger.info(f"Export completed: {successful_exports}/{total_exports} files exported successfully")
        
        # Log failed exports
        failed_exports = [name for name, success in export_results.items() if not success]
        if failed_exports:
            logger.warning(f"Failed exports: {failed_exports}")
            
    except Exception as e:
        logger.error(f"Error during data export: {e}")
        raise


def main():
    """Main function to execute the EBP data ingestion process."""
    logger.info("Starting EBP data ingestion process...")
    
    try:
        # Initialize EBP client
        ebp = EBP()
        
        # Define data endpoints and transformations
        ebp_data = {
            "contracts": {
                'url': "/api/admin/v1/contracts",
                'transformation': transform_contracts
            },
            "areas": {
                'url': "/api/admin/v1/areas",
                'transformation': transform_areas
            },
            "buildings": {
                'url': "/api/admin/v1/buildings",
                'transformation': transform_buildings
            },
            "utility_units": {
                'url': "/api/admin/v1/utilityUnits",
                'transformation': transform_utility_units
            },
            "meters": {
                'url': "/api/admin/v1/meters",
                'transformation': transform_meters
            },
            "profiles": {
                'url': "/api/admin/v1/profiles",
                'transformation': transform_profiles
            }
        }

        # Fetch and transform data
        logger.info("Fetching data from EBP API...")
        for table_name, config in ebp_data.items():
            try:
                logger.info(f"Processing {table_name}...")
                data = ebp.fetch_data(config['url'])
                
                if data is None:
                    logger.error(f"Failed to fetch data for {table_name}")
                    continue
                    
                df = pd.DataFrame(data)
                df['loadDate'] = datetime.today()
                
                # Apply transformation
                transformed_df = config['transformation'](df)
                ebp_data[table_name]['data'] = transformed_df
                
                logger.info(f"Successfully processed {table_name}: {len(transformed_df)} records")
                
            except Exception as e:
                logger.error(f"Error processing {table_name}: {e}")
                ebp_data[table_name]['data'] = pd.DataFrame()

        # Extract dataframes
        dfa = ebp_data['areas']['data']
        dfb = ebp_data['buildings']['data']
        dfc = ebp_data['contracts']['data']
        dfu = ebp_data['utility_units']['data']
        dfm = ebp_data['meters']['data']
        dfp = ebp_data['profiles']['data']

        # Add areaId to utility units by matching with buildings
        if not dfu.empty and not dfb.empty and 'buildingId' in dfu.columns and 'areaId' in dfb.columns:
            logger.info("Adding areaId to utility units...")
            building_area_map = dfb.set_index('buildingId')['areaId'].to_dict()
            dfu['areaId'] = dfu['buildingId'].map(building_area_map)
            logger.info(f"Added areaId to {dfu['areaId'].notna().sum()} utility units")
        else:
            logger.warning("Cannot add areaId to utility units: missing required columns or empty dataframes")

        # Apply data filtering
        filter_words = os.getenv('FILTER_WORDS', 'delete,geloescht,loeschen,lösch,ZEV EMD').split(',')
        logger.info(f"Applying data filters with words: {filter_words}")
        
        # Filter areas first
        dfa = apply_data_filters(dfa, filter_words, 'areaName')
        
        if not dfa.empty:
            # Get area IDs to filter other dataframes
            valid_area_ids = set(dfa['areaId'].tolist())
            
            # Filter other dataframes by areaId
            for df_name, df in [('contracts', dfc), ('utility_units', dfu), ('buildings', dfb)]:
                if not df.empty and 'areaId' in df.columns:
                    original_count = len(df)
                    df = df[df['areaId'].isin(valid_area_ids)].reset_index(drop=True)
                    filtered_count = len(df)
                    logger.info(f"Filtered {df_name}: {original_count} -> {filtered_count} records")
                    
                    # Update the dataframe
                    if df_name == 'contracts':
                        dfc = df
                    elif df_name == 'utility_units':
                        dfu = df
                    elif df_name == 'buildings':
                        dfb = df

        # Fetch manager data
        logger.info("Fetching manager data...")
        dfam = ebp.get_managers(dfc)
        dfam['loadDate'] = datetime.today()
        
        # Prepare data for export
        data_to_export = {
            'areas': dfa,
            'contracts': dfc,
            'buildings': dfb,
            'utility_units': dfu,
            'meters': dfm,
            'managers': dfam,
            'profiles': dfp
        }
        
        # Export all data
        export_all_data(data_to_export)
        
        logger.info("EBP data ingestion process completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise


if __name__ == "__main__":
    main()

