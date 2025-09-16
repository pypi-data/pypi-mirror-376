import os
import json
import webbrowser

import pandas as pd
import pyworkflow.viewer as pwviewer
from pyworkflow.protocol import params
from toxCSM.protocols.protocol_toxCSM import ProtChemToxCSM
from pathlib import Path

class JsonViewer(pwviewer.Viewer):
    _label = 'JSON Data Viewer'
    _environments = [pwviewer.DESKTOP_TKINTER]
    _targets = []

    def _visualize(self, json_file, **kwargs):
        json_path = os.path.abspath(json_file)
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        data = self.read_json(json_path)
        if not data:
            raise ValueError(f"No data found in JSON file: {json_path}")

        html_content = self.create_html(data)
        html_path = self.save_html(html_content, json_path)
        self.display_html(html_path)

    def read_json(self, json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data

    def create_html(self, data):
        html_content = "<html><head><title> Toxicity Prediction</title></head><body>"
        html_content += "<h1>Toxicity Prediction</h1>"
        html_content += "<pre>" + json.dumps(data, indent=4) + "</pre>"
        html_content += "</body></html>"
        return html_content

    def save_html(self, html_content, json_path):
        html_path = os.path.splitext(json_path)[0] + '.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        return html_path

    def display_html(self, html_path):
        webbrowser.open_new_tab(f'file://{os.path.realpath(html_path)}')


class ProtChemToxCSMViewer(pwviewer.ProtocolViewer):
    """ Viewer for ProtChemToxCSM Protocol """
    _label = 'View ToxCSM Analysis Results'
    _targets = [ProtChemToxCSM]

    def __init__(self, **args):
        super().__init__(**args)

    def _defineParams(self, form):
        form.addSection(label='ToxCSM Analysis Data')
        group_json = form.addGroup('JSON Data')
        group_json.addParam('displayJson', params.LabelParam,
                            label='Open JSON file: ',
                            help='Click to open and view the JSON data containing the ToxCSM results.')
        
        group_detail = form.addGroup('Detailed Information')
        group_detail.addParam('displayDetail', params.LabelParam,
                              label='View Detailed Information:',
                              help='Click to view more detailed information in the webpage')

        group_json = form.addGroup('CSV detailed Data')
        group_json.addParam('displayCSV', params.LabelParam,
                            label='Open CSV file: ',
                            help='Click to open and view the CSV detailed information from the ToxCSM web page.')

    def _getVisualizeDict(self):
        return {
            'displayJson': self.showJson,
            'displayDetail': self.getDetailUrl,
            'displayCSV': self.get_results,
        }
    
    def getDetailUrl(self, paramName=None):
        filename='job_id.txt'
        txt_file=self.protocol._getExtraPath(filename)
        with open(txt_file, 'r') as file:
            job_id = file.read().strip()
        url = f"https://biosig.lab.uq.edu.au/toxcsm/prediction_results/{job_id}"
        webbrowser.open_new_tab(url)


    def showJson(self, paramName=None):
        json_file = self.getJsonFile()
        return JsonViewer(project=self.getProject())._visualize(json_file)

    def getJsonFile(self):
        return self.protocol._getExtraPath("toxCSM_results.json")


    def get_results(self, paramName=None):
        #todo this goes to tmp folder even though im forcing the normal one
        print(">>> Protocol working dir:", self.protocol.getWorkingDir())
        print(">>> Extra path resolved as:", self.protocol._getExtraPath("toxCSM_detailedInfo.csv"))

        csv_path = self.protocol._getExtraPath("toxCSM_detailedInfo.csv")
        print(f"CSV path: {csv_path}")

        df = self.read_csv_to_dataframe(csv_path)

        if df is not None:
            html_table = self.dataframe_to_html(df)
            self.save_html_file(html_table)
        else:
           print("No data available to display.")

    def read_csv_to_dataframe(self, csv_path):
        try:
            df = pd.read_csv(csv_path, sep=',', usecols=lambda col: col != 'Unnamed: 0')
            print("DataFrame loaded:\n", df)
            return df
        except pd.errors.ParserError as e:
            print(f"Error reading CSV: {e}")
            return None
        except FileNotFoundError:
            print(f"CSV file not found: {csv_path}")
            return None

    def dataframe_to_html(self, df):
        html_table = df.to_html(classes='table table-striped', index=False)
        styled_html = f"""
        <style>
            .table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .table th, .table td {{
                text-align: center;
                padding: 8px;
                border: 1px solid #ddd;
            }}
        </style>
        {html_table}
        """
        return styled_html

    def save_html_file(self, html_content):
        html_path = self.protocol._getExtraPath("toxCSM_detailedInfo.html")
        with open(html_path, 'w') as f:
            f.write(html_content)
        html_file = Path(html_path).resolve()
        print(f"HTML saved at: {html_file}")
        webbrowser.open(f'file://{html_file}')



    