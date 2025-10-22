import pandas as pd
import matplotlib.pyplot as plt
from shiny import App, reactive, render, ui
from functools import lru_cache

try:
    # This will succeed only in the browser (Pyodide)
    from shinylive import open_url
    IN_BROWSER = True
except ImportError:
    IN_BROWSER = False

def read_csv_url(url, **kwargs):
    """
    Load a CSV either locally or in the browser via Pyodide.
    """
    if IN_BROWSER:
        # Use Pyodide-friendly open_url
        with open_url(url) as f:
            return pd.read_csv(f, **kwargs)
    else:
        # Normal local read
        return pd.read_csv(url, **kwargs)

# Hydrologic Timeseries
river_files = {
    "Pullayup": "https://uw-psi.github.io/shinyapp/data/Pullayup.csv",
    "Snohomish": "https://uw-psi.github.io/shinyapp/data/Snohomish.csv",
    "Green": "https://uw-psi.github.io/shinyapp/data/Green.csv",
    "Samish": "https://uw-psi.github.io/shinyapp/data/Sammish.csv",
    "Stillaguamish": "https://uw-psi.github.io/shinyapp/data/Stillaguamish.csv",
    "Hoko": "https://uw-psi.github.io/shinyapp/data/Hoko.csv",
    "Elwha": "https://uw-psi.github.io/shinyapp/data/Elwha.csv",
    "Deschutes": "https://uw-psi.github.io/shinyapp/data/Deschutes.csv",
}
sample_df = read_csv_url(river_files["Pullayup"])
hydro_variable_options = [col for col in sample_df.columns if col not in ("Year", "Day", "Loop", "Step")]
#velma datasets
velma_files = {
    "flow2011": "https://uw-psi.github.io/shinyapp/data/velma_monthly_flow_stats_2011.csv",
    "totC2011": "https://uw-psi.github.io/shinyapp/data/velma_monthly_C_stats_2011.csv"
    # "temp2011": "https://uw-psi.github.io/shinyapp/data/velma_monthly_temp_stats_2011.csv",
    # "totN2011": "https://uw-psi.github.io/shinyapp/data/velma_monthly_totN_stats_2011.csv",

}
# Landcover Change Datasets
lcc_data = {
    'counties': "https://uw-psi.github.io/shinyapp/data/diffed_counties.csv",
    'wrias': "https://uw-psi.github.io/shinyapp/data/diffed_wrias.csv",
    'velma': "https://uw-psi.github.io/shinyapp/data/diffed_velma.csv"
}
region_type_options = ["County", "WRIA", "VELMA watershed"]

land_cover_colors = {
    "Open Space": "#FFBEBE",
    "Low Intensity": "#FF7F7F",
    "Medium Intensity": "#E60000",
    "High Intensity": "#730000",
    "Forest": "#267300",
    "Agriculture": "#FFEBAF"
}

#cache datasets to avoid redownloading
@lru_cache
def load_lcc_dataset(name):
    return read_csv_url(lcc_data[name])

#####edit here (1 and 2) if you need to make new drop down labels ######
#1) load data
df_counties = load_lcc_dataset("counties")
df_wrias = load_lcc_dataset("wrias")
df_velma = load_lcc_dataset("velma")
#2) get unique region names for dropdowns
county_list = df_counties["Feature_Name"].unique().tolist()
wria_list = df_wrias["Feature_Name"].unique().tolist()
velma_list = df_velma["Feature_Name"].unique().tolist()

######################## UI #########################
# The UI section defines the app’s layout and interactive elements.
# Each tab corresponds to a different visualization dashboard.

app_ui = ui.page_fluid(
    ui.h2("PSIMF Dashboard"),
    #------ landcover dashboard tab ------
    ui.navset_tab(
        ui.nav_panel(
            "Landcover Dashboard",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_radio_buttons("region_type", "Select Region Type", choices=["County", "WRIA", 'VELMA watershed']),
                    ui.output_ui("region_selector")
                ),
                ui.navset_card_tab(
                    ui.nav_panel(
                        "Difference",
                        ui.output_plot("plot_lcc", height="400px")
                    ),
                    ui.nav_panel(
                        "Total Area",
                        ui.output_plot("plot_lcc_area", height="400px")
                    )
                )
            )
        ),
        #----------------

        #------ VELMA Monthly Explorer tab ------
        ui.nav_panel(
            "VELMA Monthly Explorer",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_radio_buttons(
                        "velma_var",
                        "Select Variable",
                        choices={
                            "flow2011": "Flow",
                            "temp2011": "Temperature",
                            "totN2011": "Total Nitrogen",
                            "totC2011": "Total Carbon"
                        }
                    ),
                    ui.input_select("velma_watershed", "Select Watershed", choices=read_csv_url(velma_files["flow2011"])["Watershed"].unique().tolist())
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("Monthly Min/Max/Mean Timeseries"),
                        ui.output_plot("velma_monthly_plot", height="500px"),
                    )
                )
            )
        ),
        #----------------
        #------ Hydrologic Explorer tab ------
        ui.nav_panel(
            "Hydrologic Explorer",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select("river", "Select River Mouth", choices=list(river_files.keys())),
                    ui.input_select("variable", "Select Variable", choices=hydro_variable_options),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("Timeseries Summary"),
                        ui.output_plot("timeseries_plot", height="500px"),
                    )
                )
            )
        ),
        #----------------
        #------ Embedded Visuals ------
        ui.nav_panel(
            "VELMA SSM Visual",
            ui.tags.iframe(
                src="https://uw-psi.github.io/visuals/velma_ssm(2).html",
                width="100%",
                height="600",
                style="border:none;"
            )
        ),
        ui.nav_panel(
            "LCC",
            ui.tags.iframe(
                src="https://uw-psi.github.io/visuals/landcover_change.html",
                width="100%",
                height="600",
                style="border:none;"
            )   
        )
    ) 
)
 ######################### Server #########################
 # The server function defines all reactive computations and plots that respond to user input in the UI.
def server(input, output, session):
    ### landcover dashboard fuctions ###
    @render.ui
    def region_selector():
        if input.region_type() == "County":
            return ui.input_select("region_name", "Select County", choices=county_list)
        elif input.region_type() == "VELMA watershed":
            return ui.input_select("region_name", "Select VELMA watershed", choices=velma_list)
        else:
            return ui.input_select("region_name", "Select WRIA", choices=wria_list)

    def make_velma_plot(df, watershed, variable):
        df = df[df["Watershed"] == watershed]
        pivot = df.pivot_table(
            index="Month",
            columns="Year",
            values=variable
        )
        ax = pivot.plot(
            kind="line",
            marker='o'
        )
        ax.set_ylabel(variable)
        ax.set_xlabel("Month")
        ax.set_title(f"{variable} in {watershed} Watershed")
        ax.legend(title="Year", bbox_to_anchor=(1.05, 1), loc='upper left')
        return ax
    
    def make_lcc_plot(df, region_name):
        df = df[df["Feature_Name"] == region_name]
        pivot = df.pivot_table(
            index="Year",
            columns="Landcover_Class",
            values="diff_dev",
            fill_value=0
        )
        ax = pivot.plot(
            kind="bar",
            stacked=True,
            color=[land_cover_colors.get(c, "#333333") for c in pivot.columns]
        )
        ax.set_ylabel("Difference in km² from baseline (2015)")
        ax.set_xlabel("Year")
        ax.set_title(f"Landcover Change in {region_name}")
        ax.legend(title="Landcover Class", bbox_to_anchor=(1.05, 1), loc='upper left')
        return ax
    
    def make_lcc_area_plot(df, region_name):
        df = df[df["Feature_Name"] == region_name]
        pivot = df.pivot_table(
            index="Year",
            columns="Landcover_Class",
            values="Developable_Area_km2",
            aggfunc="sum",
            fill_value=0
        )
        ax = pivot.plot(
            kind="bar",
            stacked=True,
            color=[land_cover_colors.get(c, "#333333") for c in pivot.columns]
        )
        ax.set_ylabel("Developable area in km²")
        ax.set_xlabel("Year")
        ax.set_title(f"Landcover Change in {region_name}")
        ax.legend(title="Landcover Class", bbox_to_anchor=(1.05, 1), loc='upper left')
        return ax
    
    @reactive.Calc
    def selected_region_type():
        """Tracks the currently selected region type."""
        return input.region_type()

    @reactive.Calc
    def selected_dataset():
        """Returns the appropriate dataset based on region type."""
        if selected_region_type() == "County":
            return load_lcc_dataset("counties")
        elif selected_region_type() == "VELMA watershed":
            return load_lcc_dataset("velma")
        else:
            return load_lcc_dataset("wrias")

    @render.plot
    def plot_lcc():
        return make_lcc_plot(selected_dataset(), input.region_name())
    
    @render.plot
    def plot_lcc_area():
        return make_lcc_area_plot(selected_dataset(), input.region_name())
    
    ### VELMA Monthly Explorer functions ###
    @reactive.Calc
    def hydro_data():
        file_path = river_files[input.river()]
        return read_csv_url(file_path)

    @reactive.Calc
    def hydro_summary():
        df = hydro_data()
        var = input.variable()
        summary = df.groupby("Year")[var].agg(["min", "max", "mean"]).reset_index()
        return summary

    @render.plot
    def timeseries_plot():
        df = hydro_summary()
        fig, ax = plt.subplots()
        ax.plot(df["Year"], df["mean"], label="Mean", color="blue")
        ax.fill_between(df["Year"], df["min"], df["max"], color="blue", alpha=0.2, label="Min-Max Range")
        ax.set_ylabel(input.variable())
        ax.set_xlabel("Year")
        ax.set_title(f"{input.variable()} in {input.river()} River")
        ax.legend()
        return ax

#this line combines the ui and server to create the app
app = App(app_ui, server)
