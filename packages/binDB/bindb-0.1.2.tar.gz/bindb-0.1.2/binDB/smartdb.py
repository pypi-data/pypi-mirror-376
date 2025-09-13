import json
import os
import time
import pycountry
import pycountry_convert
import random
from typing import Optional, List, Dict

class SmartBinDB:
    def __init__(self):
        self.COUNTRY_JSON_DIR = os.path.join(os.path.dirname(__file__), "data")
        self.BIN_INDEX = {}
        self.COUNTRY_DATA = {}
        self.START_TIME = time.time()
        self.load_data() # Load data synchronously on initialization

    def load_file(self, file_path: str, country_code: str) -> bool:
        for attempt in range(3):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                self.COUNTRY_DATA[country_code] = data
                for entry in data:
                    if 'bin' in entry:
                        self.BIN_INDEX[entry['bin']] = entry
                return True
            except Exception as e:
                print(f"Error loading {file_path} (attempt {attempt + 1}): {str(e)}")
                time.sleep(0.1)
        return False

    def load_data(self):
        if not os.path.exists(self.COUNTRY_JSON_DIR):
            print(f"Directory {self.COUNTRY_JSON_DIR} does not exist")
            return
        
        for filename in os.listdir(self.COUNTRY_JSON_DIR):
            if filename.lower().endswith('.json'):
                country_code = filename.replace('.json', '').upper()
                file_path = os.path.join(self.COUNTRY_JSON_DIR, filename)
                self.load_file(file_path, country_code)
        
        # No need for async.gather or results processing here, as it's synchronous now.
        # The original code had a 'failed' count, but for synchronous loading,
        # individual load_file calls will print errors.

    def get_country_info(self, country_code: str) -> dict:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        if not country:
            return {
                "A2": country_code.upper(),
                "A3": "",
                "N3": "",
                "Name": "",
                "Cont": ""
            }
        try:
            continent_code = pycountry_convert.country_alpha2_to_continent_code(country.alpha_2)
            continent = pycountry_convert.convert_continent_code_to_continent_name(continent_code)
        except Exception as e:
            print(f"Error getting continent for {country_code}: {str(e)}")
            continent = ""
        return {
            "A2": country.alpha_2,
            "A3": country.alpha_3,
            "N3": country.numeric,
            "Name": country.name,
            "Cont": continent
        }

    def format_entry(self, entry: dict) -> dict:
        country_code = entry.get('country_code', '').upper()
        country_info = self.get_country_info(country_code)
        return {
            "bin": entry.get('bin', ''),
            "brand": entry.get('brand', ''),
            "category": entry.get('category', ''),
            "CardTier": f"{entry.get('category', '')} {entry.get('brand', '')}".strip(),
            "country_code": country_code,
            "Type": entry.get('type', ''),
            "country_code_alpha3": entry.get('country_code_alpha3', ''),
            "Country": country_info,
            "issuer": entry.get('issuer', ''),
            "phone": entry.get('phone', ''),
            "type": entry.get('type', ''),
            "website": entry.get('website', '')
        }

    def get_bins_by_bank(self, bank: str, limit: Optional[int] = None) -> dict:
        # Data is loaded in __init__, so no need to check self.COUNTRY_DATA here
        if not self.COUNTRY_DATA:
            return {
                "status": "error",
                "message": f"Data directory not found or empty: {self.COUNTRY_JSON_DIR}"
            }
        matching_bins = []
        for data in self.COUNTRY_DATA.values():
            for entry in data:
                if 'issuer' in entry and bank.lower() in entry['issuer'].lower():
                    matching_bins.append(self.format_entry(entry))
        if not matching_bins:
            return {
                "status": "error",
                "message": f"No matches found for bank: {bank}"
            }
        if limit is not None:
            matching_bins = matching_bins[:limit]
        return {
            "status": "SUCCESS",
            "data": matching_bins,
            "count": len(matching_bins),
            "filtered_by": "bank",
            "Luhn": True
        }

    def get_bins_by_country(self, country: str, limit: Optional[int] = None, randomize: bool = False) -> dict:
        # Data is loaded in __init__, so no need to check self.COUNTRY_DATA here
        if not self.COUNTRY_DATA:
            return {
                "status": "error",
                "message": f"Data directory not found or empty: {self.COUNTRY_JSON_DIR}"
            }
        country = country.upper()
        
        matching_bins = []
        if country == 'US':
            for country_code in ['US', 'US1', 'US2']:
                if country_code in self.COUNTRY_DATA:
                    matching_bins.extend(self.COUNTRY_DATA[country_code])
        elif country in self.COUNTRY_DATA:
            matching_bins = self.COUNTRY_DATA[country]

        if not matching_bins:
            return {
                "status": "error",
                "message": f"No data found for country code: {country}"
            }

        if country == 'US':
            if limit is None:
                limit = 1000
            if limit > 8000:
                return {
                    "status": "error",
                    "message": "Maximum limit allowed for US is 8000"
                }

        if randomize:
            if limit is not None and limit < len(matching_bins):
                result_bins = random.sample(matching_bins, limit)
            else:
                # If limit is larger than available data, shuffle all available data
                result_bins = random.sample(matching_bins, len(matching_bins))
        else:
            if limit is not None:
                result_bins = matching_bins[:limit]
            else:
                result_bins = matching_bins

        formatted_data = [self.format_entry(entry) for entry in result_bins]
        
        return {
            "status": "SUCCESS",
            "data": formatted_data,
            "count": len(formatted_data),
            "filtered_by": "country",
            "Luhn": True
        }

    def get_bin_info(self, bin: str) -> dict:
        # Data is loaded in __init__, so no need to check self.BIN_INDEX here
        if not self.BIN_INDEX:
            return {
                "status": "error",
                "message": f"Data directory not found or empty: {self.COUNTRY_JSON_DIR}"
            }
        if bin in self.BIN_INDEX:
            return {
                "status": "SUCCESS",
                "data": [self.format_entry(self.BIN_INDEX[bin])],
                "count": 1,
                "filtered_by": "bin",
                "Luhn": True
            }
        return {
            "status": "error",
            "message": f"No matches found for BIN: {bin}"
        }

    def get_bins(self, country_code: Optional[str] = None, limit: int = 10, randomize: bool = False) -> dict:
        if not self.COUNTRY_DATA:
            return {"status": "error", "message": "No data available."}

        bins_data = []
        if country_code:
            country_code = country_code.upper()
            if country_code in self.COUNTRY_DATA:
                bins_data = self.COUNTRY_DATA[country_code]
            else:
                return {"status": "error", "message": f"No data for country: {country_code}"}
        else:
            # Consolidate all BINs from all countries
            for country_bins in self.COUNTRY_DATA.values():
                bins_data.extend(country_bins)

        if not bins_data:
            return {"status": "error", "message": "No BINs found."}

        if randomize:
            num_to_sample = min(limit, len(bins_data))
            selected_bins = random.sample(bins_data, num_to_sample)
        else:
            selected_bins = bins_data[:limit]

        formatted_bins = [self.format_entry(bin_info) for bin_info in selected_bins]

        return {
            "status": "SUCCESS",
            "data": formatted_bins,
            "count": len(formatted_bins),
            "filtered_by": "country" if country_code else "all_countries",
            "Luhn": True
        }

    def get_total_bins_count(self) -> int:
        return len(self.BIN_INDEX)

    def get_country_bin_counts(self) -> dict:
        counts = {country: len(bins) for country, bins in self.COUNTRY_DATA.items()}
        return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
