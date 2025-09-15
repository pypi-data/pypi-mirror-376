from Levenshtein import distance
import re
import csv

class PostProcessor:
    def __init__(self):
        self.delimiter = ','  

    def _write_to_csv(self, data, output_csv):
        """
        Write the processed data to a CSV file.
        """
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys(),delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data)
            print(f"Processed data written to {output_csv}")
        
    def _remove_one_header(self, field_value: str, header: str) -> str:
        def treat_hyphens(field_value: str) -> str:
            # Replace all dash variants with a standard hyphen
            return re.sub(r'[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D\-]', '-', field_value)
        field_value = treat_hyphens(field_value)
        match = re.search(fr'{header}\s*:', field_value, re.IGNORECASE)
        if match:
            field_value = field_value[match.end():].strip()
            field_value = field_value.split(header)[-1].strip()
        return field_value
        
    def _remove_title_parts(self, row: dict) -> dict:
        updated_inventory_data = {}
        for k,v in row.items():
            updated_inventory_data[k] = self._remove_one_header(v,k)
        return updated_inventory_data

    def _update_one_entry(self, row: dict) -> dict:
        """
        Update a single entry in the row based on specific rules.
        This method should be overridden by subclasses to implement custom logic.
        """
        return row

    def postprocess(self, input_csv, output_csv):
        """
        Post-process the data after OCR.
        """
        with open(input_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            input_data = [row for row in reader]
        updated_data = []
        for row in input_data:
            updated_row = self._remove_title_parts(row)
            updated_row = self._update_one_entry(updated_row)
            updated_data.append(updated_row)
        
        self._write_to_csv(updated_data, output_csv) 

class BenchmarkingPostProcessor(PostProcessor):
    def __init__(self):
        super().__init__()
        self._empty_marker = ''
        print('Benchmarking postprocessor initialized.')

    def _handle_masse(self, row: dict) -> str:
        if 'Gewicht' in row and row['Gewicht'] != '' and 'Maße' in row:
            return row['Maße'], row['Gewicht'] # treat cases where gewicht is handled by ocr engine (ie Mistral)
        masse_str = row.get('Maße', '')    
        # Extract all cohesive numbers before 'g' as weight, others as measurement
        weights = []
        measurements = []

        # Find all numbers followed by optional whitespace and 'g' (weight)
        weight_matches = re.findall(r'(\d+(?:[.,]\d+)?\s*g)', masse_str)
        weights.extend(weight_matches)

        # Remove weights from the string to avoid double counting
        masse_str_no_weights = re.sub(r'\d+(?:[.,]\d+)?\s*g', '', masse_str)

        # Return measurements and weight as a tuple of concatenated strings
        weight_str = ', '.join(weights) if weights else self._empty_marker

        masse_str_no_weights = self._remove_one_header(masse_str_no_weights, 'Gewicht')

        return masse_str_no_weights, weight_str

    def _update_one_entry(self, row: dict) -> dict:
        """
        Update a single entry in the row based on benchmarking rules.
        """
        updated_row = {}
        for k, v in row.items():
            if v is None or v.strip() == '':
                updated_row[k] = self._empty_marker
            else:
                updated_row[k] = v.strip()

        updated_row['filename'] = row.get('source_file', self._empty_marker)
        del updated_row['source_file']
        updated_row['Inventarnummer'] = row.get('Inv. Nr.', self._empty_marker)
        del updated_row['Inv. Nr.']
        updated_row['erworben am'] = row.get('am', self._empty_marker)
        del updated_row['am']
        updated_row['Versicherungswert'] = row.get('Vers.-Wert', self._empty_marker)
        del updated_row['Vers.-Wert']
        measurements, weight = self._handle_masse(row)
        updated_row['Masse'] = measurements
        updated_row['Gewicht'] = weight
        del updated_row['Maße']
        return updated_row

class SchmuckPostProcessor(PostProcessor):
    def __init__(self):
        print("Using SchmuckPostProcessor for production mode.")
        super().__init__()
        self._empty_marker = 'Unbekannt'
        self.delimiter = ';'  # Use semicolon as delimiter for Schmuck CSV
        # spacy.cli.download("de_core_news_sm")
        # self.nlp = spacy.load("de_core_news_sm")


    def _extract_price_and_currency(self, price_str: str) -> tuple:
        def is_donated(price_str):
            if distance(price_str.strip(), 'Stiftung') <= 1:
                return True
            if distance(price_str.strip(), 'Geschenk') <= 1:
                return True
            return False

        if not price_str or price_str.strip() == '':
            price = 'Unbekannt'
        else:
            price = re.sub(r'[^\d]', '', price_str)  # Remove non-digit characters

        if is_donated(price_str):
            return 0, 'Deutsche Mark'

        if 'DM' in price_str or 'Dm' in price_str:
            return price, 'Deutsche Mark'
        if 'M' in price_str:
            return price, 'Reichsmark (Deutsches Reich)'

        return price, 'Deutsche Mark'
            

    def _is_bought(self, row: dict) -> bool:
        erworben = row.get('erworben von', '').strip()
        if erworben.lower() == 'stiftung':
            return False
        if not row['Preis'] or row['Preis'].strip() == '':
            return False
        return True

    def _extract_notes(self, row: dict) -> str | None:
        notes = row.get('Literatur')
        if not self._is_bought(row) and row.get('erworben von') != '':
            notes += f"Angaben aus dem Inventarkartenfeld 'erworben von': {row.get('erworben von')}"
        return notes

    def _extract_standort(self, standort: str) -> str: 
        if not standort or standort.strip() == '':
            return self._empty_marker
        return "alter Standort: " + standort 
    

    def _extract_erwerb(self, row: dict) -> list:
        # erworben_doc = self.nlp(row.get('erworben von', ''))
        # persons = [ent.text for ent in erworben_doc.ents if ent.label_ == 'PER']
        # places = [ent.text for ent in erworben_doc.ents if ent.label_ == 'LOC']
        # TODO
        erworben_str = row.get('erworben von')
        preis_str = row.get('Preis')
        matches = re.search("Hersteller|Entwurf|Ausführung|Herst.|Entw.|Ausf.", erworben_str, flags=re.IGNORECASE)
        if not matches:
            row = row
        return row

    def _extract_description(self, row: dict) -> str:
        DEFAULT_DESCRIPTION = 'Dieses Schmuckstück ist aus dem historischen Schmuckinventar der Kunstgewerbeschule Pforzheim.'
        beschreibung = row.get('Beschreibung', DEFAULT_DESCRIPTION)
        if not beschreibung or beschreibung.strip() == '':
            beschreibung = DEFAULT_DESCRIPTION
        return beschreibung
    

    def _update_one_entry(self, row: dict) -> dict:
        """
        Update a single entry in the row based on rules.
        """
        unchanged_keys = []
        def get_or_default(row: dict, key: str, default=self._empty_marker) -> str:
            value = row.get(key, '')
            if value is None or value.strip() == '':
                return default
            return value

        updated_row = {}
        for k in unchanged_keys:
            updated_row[k] = get_or_default(row, k)

        updated_row['object_title'] = get_or_default(row, 'Gegenstand')
        updated_row['object_type'] = "Schmuck"
        updated_row['inventory_number'] = get_or_default(row, 'Inv. Nr.')

        updated_row['remarks_short'] = get_or_default(row, 'source_file')
        updated_row['remarks_long'] = get_or_default(row, 'Maße')
        updated_row['literature_title1'] = get_or_default(row, 'Literatur')


        updated_row['abode_regular'] = self._extract_standort(row.get('Standort'))
        updated_row["abode_actual"] = "Schmuckmuseum Pforzheim"

        updated_row['material_separate'] = get_or_default(row, 'Material')
        updated_row['object_description'] = self._extract_description(row)

        insurance_value, insurance_value_currency = self._extract_price_and_currency(row.get('Vers.-Wert', ''))
        updated_row['worth_insurance_value'] = insurance_value
        updated_row['worth_insurance_unit'] = insurance_value_currency

        # updated_row['Notizen'] = self._extract_notes(row) or empty_marker
        updated_row['exhibition_name1'] = get_or_default(row, 'Ausstellungen')

        updated_row['image_name1'] = get_or_default(row,'Foto Notes')
        updated_row['image_owner1'] = 'Schmuckmuseum Pforzheim'
        updated_row['image_rights1'] = 'RR-R'
        updated_row['image_visible1'] = 'y'
        updated_row['image_main1'] = 'y'


        updated_row['form_designed_when1'] = get_or_default(row, 'Datierung')
        updated_row['form_designed_who1'] = self._empty_marker
        updated_row['form_designed_where1'] = get_or_default(row, 'Herkunft')

        # internal fields
        updated_row['acquisition_type'] = self._empty_marker
        updated_row['acquisition_name'] = 'Erwerb'
        updated_row['acquisition_source_name'] = get_or_default(row, 'erworben von')
        updated_row['acquisition_date'] = get_or_default(row, 'am', default='3000-01-01')
        acquisition_price, acquisition_price_currency = self._extract_price_and_currency(row.get('Preis', ''))
        updated_row['acquisition_price'] = acquisition_price
        updated_row['acquisition_price_currency'] = acquisition_price_currency
        updated_row['acquisition_note'] = "Art des Zugangs ist zu überprüfen."
        
        # copied from acquisition for potential publication
        updated_row['received_ownership_when1'] = updated_row['acquisition_date']
        updated_row['received_ownership_who1'] = updated_row['acquisition_source_name'] 
        updated_row['received_ownership_where1'] = 'Pforzheim'
        updated_row['received_ownership_where_sure1'] = 'n'

        return updated_row