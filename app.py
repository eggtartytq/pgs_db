import sqlite3
from shiny import App, ui, render, reactive
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('pgs.db')

def get_table_data(table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    if 'filename' in df.columns:
        df = df.drop(columns=['filename'])
    return df

def get_table_names():
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    return pd.read_sql_query(query, conn)['name'].tolist()

def execute_custom_query(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame({'Error': [str(e)]})

app_ui = ui.page_fluid(
    ui.h1("PGS Database Viewer"),
    ui.row(
        ui.column(3,
            ui.div(
                ui.input_action_button("reset", "Reset to Main Page", class_="btn-primary"),
                ui.input_text("custom_query", "Enter your SQL query here:", width="100%"),
                ui.input_action_button("run_query", "Run Query", class_="btn-success"),
                ui.output_text("selected_table_text"),
                style="background-color: lightblue; padding: 20px; height: 100vh;"
            )
        ),
        ui.column(9,
            ui.output_ui("table_output")
        )
    ),
    ui.input_action_button("dummy", "dummy", style="display: none;")
)

def server(input, output, session):
    table_names = get_table_names()
    selected_table = reactive.Value("pgs_dict")
    custom_query_result = reactive.Value(None)

    @output
    @render.text
    def selected_table_text():
        if custom_query_result.get() is not None:
            return "Custom query result"
        return f"Selected table: {selected_table.get()}"

    @output
    @render.ui
    def table_output():
        if custom_query_result.get() is not None:
            table_data = custom_query_result.get()
        else:
            table_data = get_table_data(selected_table.get())
        
        if selected_table.get() == "pgs_dict" and custom_query_result.get() is None:
            def create_button(pgs_id):
                return ui.a(pgs_id, href="#", onclick=f"Shiny.setInputValue('selected_pgs_id', '{pgs_id}'); return false;")
            
            table_data['pgs_id'] = table_data['pgs_id'].apply(create_button)
        
        # Convert DataFrame to HTML table with custom styling
        table_html = table_data.to_html(escape=False, index=False, classes=['table', 'table-bordered'])
        
        # Add custom CSS for table styling
        custom_css = """
        <style>
        .table th, .table td {
            border-right: 1px solid #dee2e6;
            text-align: right;
        }
        .table th:first-child, .table td:first-child {
            text-align: left;
        }
        </style>
        """
        
        return ui.HTML(custom_css + table_html)

    @reactive.Effect
    @reactive.event(input.reset)
    def reset_to_main():
        selected_table.set("pgs_dict")
        custom_query_result.set(None)

    @reactive.Effect
    @reactive.event(input.selected_pgs_id)
    def handle_pgs_id_click():
        selected_pgs_id = input.selected_pgs_id()
        if selected_pgs_id in table_names:
            selected_table.set(selected_pgs_id)
            custom_query_result.set(None)

    @reactive.Effect
    @reactive.event(input.run_query)
    def run_custom_query():
        query = input.custom_query()
        result = execute_custom_query(query)
        custom_query_result.set(result)

app = App(app_ui, server)
