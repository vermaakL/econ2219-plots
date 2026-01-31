import pandas as pd
import matplotlib.pyplot as plt

class CountryData:
    """
    Class to manage and visualize economic data for a single country.

    Supports:
        - GDP
        - GDP per capita
        - Inflation
        - Unemployment
        - Long-term government bond yields
    """

    def __init__(self, name):
        
        # Initialize country object and placeholders for data
        self.name = name
        self.gdp = None
        self.gdp_per_capita = None
        self.inflation = None
        self.unemployment = None
        self.bond_yields = None
    
    # Class constant: EU member states
    EU_COUNTRIES = [
        "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
        "Slovenia", "Spain", "Sweden"
    ]


    # -------------------------------
    # Data loading methods
    # -------------------------------


    def get_gdp(self, path="DB/Penn World Table.csv"):
        
        # If this is the European Union, compute the total GDP across all member states
        if self.name == "European Union":
            all_dfs = []
            for country in CountryData.EU_COUNTRIES:   # use class variable here
                try:
                    temp = CountryData(country)
                    temp.get_gdp(path)  # recursively load GDP for this country
                    all_dfs.append(temp.gdp)
                except Exception as e:
                    print(f"Warning: Could not load GDP for {country}: {e}")

            if not all_dfs:
                raise ValueError("No EU member state GDP data could be loaded.")

            # Merge all dataframes and sum GDP by date
            df_concat = pd.concat(all_dfs)
            self.gdp = df_concat.groupby("Date", as_index=False)["GDP"].sum()
            self.name = "European Union"
            return  # done for European Union

        # -------------------------------
        # Normal single-country GDP loading
        # -------------------------------
        df = pd.read_csv(path)
        df = df[(df["Country"] == self.name) & (df["Variable code"] == "rgdpo")]
        year_cols = [c for c in df.columns if c.isdigit()]

        df_long = df.melt(id_vars="Country", value_vars=year_cols,
                        var_name="Date", value_name="GDP")
        df_long["Date"] = pd.to_datetime(df_long["Date"], format="%Y")
        df_long["GDP"] = pd.to_numeric(df_long["GDP"], errors="coerce")

        self.gdp = df_long.dropna(subset=["GDP"]).reset_index(drop=True)

    def get_gdp_per_capita(self, path="DB/Penn World Table.csv"):

        # If this is the European Union, compute the average GDP per capita across all member states
        if self.name == "European Union":
            all_dfs = []
            for country in CountryData.EU_COUNTRIES:
                try:
                    temp = CountryData(country)
                    temp.get_gdp_per_capita(path)
                    all_dfs.append(temp.gdp_per_capita)
                except Exception as e:
                    print(f"Warning: Could not load GDP per capita for {country}: {e}")

            if not all_dfs:
                raise ValueError("No EU member state GDP per capita data could be loaded.")

            # Merge all dataframes and average GDP per capita by date
            df_concat = pd.concat(all_dfs)
            self.gdp_per_capita = df_concat.groupby("Date", as_index=False)["GDP_per_capita"].mean()
            self.name = "European Union"
            return

        # Normal single-country GDP per capita loading
        df = pd.read_csv(path)
        year_cols = [c for c in df.columns if c.isdigit()]

        # GDP data
        gdp = df[(df["Country"] == self.name) & (df["Variable code"] == "rgdpo")][["Country"] + year_cols]
        gdp_long = gdp.melt(id_vars="Country", value_vars=year_cols, var_name="Date", value_name="GDP")

        # Population data
        pop = df[(df["Country"] == self.name) & (df["Variable code"] == "pop")][["Country"] + year_cols]
        pop_long = pop.melt(id_vars="Country", value_vars=year_cols, var_name="Date", value_name="Population")

        # Merge and calculate GDP per capita
        merged = pd.merge(gdp_long, pop_long, on=["Country", "Date"], how="inner")
        merged["Date"] = pd.to_datetime(merged["Date"], format="%Y")
        merged["GDP"] = pd.to_numeric(merged["GDP"], errors="coerce")
        merged["Population"] = pd.to_numeric(merged["Population"], errors="coerce")
        merged["GDP_per_capita"] = merged["GDP"] / merged["Population"]

        # Save cleaned data
        self.gdp_per_capita = merged.dropna(subset=["GDP_per_capita"]).reset_index(drop=True)

    def get_inflation(self, path="DB/CPI.csv"):

        # If this is the European Union, compute the average GDP per capita across all member states
        if self.name == "European Union":
            all_dfs = []

            # Loop through all EU member states
            for country in CountryData.EU_COUNTRIES:
                try:
                    temp = CountryData(country)
                    temp.get_inflation(path)  # recursively load single-country inflation
                    all_dfs.append(temp.inflation)
                except Exception as e:
                    print(f"Warning: Could not load inflation for {country}: {e}")

            if not all_dfs:
                raise ValueError("No EU member state inflation data could be loaded.")

            # Merge all member state data
            df_concat = pd.concat(all_dfs, ignore_index=True)

            # Convert TIME_PERIOD to datetime (year only)
            df_concat["TIME_PERIOD"] = pd.to_datetime(df_concat["TIME_PERIOD"], format="%Y", errors="coerce")

            # Convert inflation values to numeric
            df_concat["INFLATION_YOY_PCT"] = pd.to_numeric(df_concat["INFLATION_YOY_PCT"], errors="coerce")

            # Drop extreme outliers
            df_concat = df_concat[(df_concat["INFLATION_YOY_PCT"] >= -50) & 
                                (df_concat["INFLATION_YOY_PCT"] <= 50)]

            # Only include years where at least half of EU countries have data
            counts = df_concat.groupby("TIME_PERIOD")["INFLATION_YOY_PCT"].count()
            valid_years = counts[counts >= len(CountryData.EU_COUNTRIES) / 2].index
            df_concat = df_concat[df_concat["TIME_PERIOD"].isin(valid_years)]

            # Compute the average inflation per year
            self.inflation = df_concat.groupby("TIME_PERIOD", as_index=False)["INFLATION_YOY_PCT"].mean()
            self.name = "European Union"

            return  # Done, skip the single-country logic

        # Load year-on-year inflation data for the country
        df = pd.read_csv(path)

        # Keep only rows for this country and relevant columns
        df = df[df["Reference area"] == self.name][["TIME_PERIOD", "OBS_VALUE"]]
        df = df.rename(columns={"OBS_VALUE": "INFLATION_YOY_PCT"})

        # Convert TIME_PERIOD to datetime
        df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"], errors="coerce")

        # Convert values to numeric
        df["INFLATION_YOY_PCT"] = pd.to_numeric(df["INFLATION_YOY_PCT"]
                                                , errors="coerce")

        # Save cleaned data
        self.inflation = df.dropna(subset=["TIME_PERIOD", "INFLATION_YOY_PCT"]) \
                        .sort_values("TIME_PERIOD") \
                        .reset_index(drop=True)

    def get_unemployment(self, path="DB/Unemployment.csv"):

        # If this is the European Union, use the EU data directly from the table
        if self.name == "European Union":
            df = pd.read_csv(path)
            df = df[df['STRUCTURE'] == 'DATAFLOW']   # Keep real data
            df = df[df['AGE'] == '_T']               # Only total across all ages
            df = df[df['Reference area'] == 'European Union (27 countries)']

            # Pivot so LF and EMP are separate columns
            df_pivot = df.pivot_table(
                index=['Reference area', 'TIME_PERIOD'],
                columns='LABOUR_FORCE_STATUS',
                values='OBS_VALUE',
                aggfunc='sum'
            ).reset_index()

            # Compute unemployment rate
            df_pivot['UnemploymentRate'] = (df_pivot['LF'] - df_pivot['EMP']) / df_pivot['LF'] * 100
            df_pivot['Date'] = pd.to_datetime(df_pivot['TIME_PERIOD'], format='%Y', errors='coerce')

            # Save cleaned data
            self.unemployment = df_pivot[['Reference area', 'Date', 'UnemploymentRate']] \
                                    .dropna() \
                                    .rename(columns={'Reference area': 'Country'}) \
                                    .reset_index(drop=True)
            self.name = "European Union"
            return  # Done, skip single-country logic

        # -------------------------------
        # Normal single-country unemployment
        # -------------------------------
        df = pd.read_csv(path)
        df = df[df['STRUCTURE'] == 'DATAFLOW']   # Keep real data
        df = df[df['AGE'] == '_T']               # Only total across all ages
        df = df[df['Reference area'] == self.name]

        # Pivot so LF and EMP are separate columns
        df_pivot = df.pivot_table(
            index=['Reference area', 'TIME_PERIOD'],
            columns='LABOUR_FORCE_STATUS',
            values='OBS_VALUE',
            aggfunc='sum'
        ).reset_index()

        # Compute unemployment rate
        df_pivot['UnemploymentRate'] = (df_pivot['LF'] - df_pivot['EMP']) / df_pivot['LF'] * 100
        df_pivot['Date'] = pd.to_datetime(df_pivot['TIME_PERIOD'], format='%Y', errors='coerce')

        # Save cleaned data
        self.unemployment = df_pivot[['Reference area', 'Date', 'UnemploymentRate']] \
                                .dropna() \
                                .rename(columns={'Reference area': 'Country'}) \
                                .reset_index(drop=True)

    def get_bond_yields(self, path="DB/Long-Term Interest Rates.csv"):
        """Load long-term government bond yields for the country."""

        # Use CSV name for European Union / otherwise the country name directly
        if(self.name == "European Union"):
            self.name = "Euro area (19 countries)"

        # Read CSV and keep only DATAFLOW rows
        df = pd.read_csv(path)
        df = df[df['STRUCTURE'] == 'DATAFLOW']

        # Keep only rows for this country and relevant columns
        df = df[df['Reference area'] == self.name][['Reference area', 'TIME_PERIOD', 'OBS_VALUE']].copy()

        # Convert time column to datetime (try Year-Month first, fallback to Year)
        df['Date'] = pd.to_datetime(df['TIME_PERIOD'], errors='coerce', format='%Y-%m')
        df['Date'] = df['Date'].fillna(pd.to_datetime(df['TIME_PERIOD'], errors='coerce', format='%Y'))

        # Convert bond yield values to numeric
        df['BondYield'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')

        # Drop invalid or extreme values, remove duplicates, sort by date
        df = df.dropna(subset=['Date', 'BondYield'])
        df = df[(df['BondYield'] >= -5) & (df['BondYield'] <= 50)] \
                .drop_duplicates(subset=['Date']) \
                .sort_values('Date') \
                .reset_index(drop=True)

        # Save cleaned data to object
        self.bond_yields = df.rename(columns={'Reference area': 'Country'})[['Country', 'Date', 'BondYield']]


    # -------------------------------
    # Plotting methods for a single country
    # -------------------------------


    def plot_gdp(self, ax=None):
        
        # Plot GDP over time
        if self.gdp is None:
            self.get_gdp()
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,6))
        ax.plot(self.gdp["Date"], self.gdp["GDP"] / 1e6, label=self.name)
        ax.set_ylabel("Real GDP (Million $)")
        ax.set_xlabel("Date")
        ax.set_title("Real GDP Over Time")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        return ax

    def plot_gdp_per_capita(self, ax=None):
        
        # Plot GDP per capita over time
        if self.gdp_per_capita is None:
            self.get_gdp_per_capita()
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,6))
        ax.plot(self.gdp_per_capita["Date"], self.gdp_per_capita["GDP_per_capita"] / 1e3, label=self.name)
        ax.set_ylabel("GDP per Capita (Thousand $)")
        ax.set_xlabel("Date")
        ax.set_title("GDP per Capita Over Time")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        return ax

    def plot_inflation(self, ax=None):
        
        # Plot year-on-year inflation
        if self.inflation is None:
            self.get_inflation()
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,6))
        ax.plot(self.inflation["TIME_PERIOD"], self.inflation["INFLATION_YOY_PCT"], label=self.name)
        ax.set_ylabel("Inflation (% YoY)")
        ax.set_xlabel("Date")
        ax.set_title("Year-on-Year Inflation")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        return ax

    def plot_unemployment(self, ax=None):
        
        # Plot unemployment rate over time
        if self.unemployment is None:
            self.get_unemployment()
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,6))
        ax.plot(self.unemployment["Date"], self.unemployment["UnemploymentRate"], label=self.name)
        ax.set_ylabel("Unemployment Rate (%)")
        ax.set_xlabel("Date")
        ax.set_title("Unemployment Rate Over Time")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        return ax

    def plot_bond_yields(self, ax=None):
        
        # Plot long-term bond yields
        if self.bond_yields is None:
            self.get_bond_yields()
        if ax is None:
            fig, ax = plt.subplots(figsize=(12,6))
        ax.plot(self.bond_yields["Date"], self.bond_yields["BondYield"], label=self.name)
        ax.set_ylabel("Long-Term Bond Yield (%)")
        ax.set_xlabel("Date")
        ax.set_title("Long-Term Government Bond Yields Over Time")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        return ax


    # -------------------------------
    # Plot multiple countries at once
    # -------------------------------


    @classmethod
    def plot_multiple(cls, countries, indicator="gdp"):
        
        # Plot one indicator for multiple countries on the same chart
        fig, ax = plt.subplots(figsize=(12,6))
        for name in countries:
            c = cls(name)
            plot_func = getattr(c, f"plot_{indicator}")
            plot_func(ax=ax)   # Pass the same axes to overlay
        plt.show()


# -------------------------------
# Console Interface with interactive legend
# -------------------------------

import matplotlib.pyplot as plt

def make_lines_toggleable(ax):
    """
    Makes legend entries clickable to toggle line visibility.
    """
    lines = ax.get_lines()
    legend = ax.legend()
    for legline, origline in zip(legend.get_lines(), lines):
        legline.set_picker(True)  # Enable picking on the legend line
        legline._origline = origline

    def on_pick(event):
        legline = event.artist
        origline = legline._origline
        visible = not origline.get_visible()
        origline.set_visible(visible)
        legline.set_alpha(1.0 if visible else 0.2)  # dim legend when hidden
        ax.figure.canvas.draw()

    ax.figure.canvas.mpl_connect('pick_event', on_pick)


# Map user choice to display name and method
choice_map = {
    "1": ("GDP", "plot_gdp"),
    "2": ("GDP per Capita", "plot_gdp_per_capita"),
    "3": ("Inflation", "plot_inflation"),
    "4": ("Unemployment", "plot_unemployment"),
    "5": ("Long-Term Bond Yields", "plot_bond_yields")
}

# Print options
print("Select an economic indicator to plot:")
for number, (display_name, _) in choice_map.items():
    print(f"{number}: {display_name}")

# Get user choice
choice = input("Enter the number of your choice: ").strip()
if choice not in choice_map:
    print("Invalid choice.")
    exit()
indicator_method_name = choice_map[choice][1]

# Get countries from user, normalize capitalization
countries_input = input("Enter the countries (comma-separated): ").strip()
countries = [c.strip().title() for c in countries_input.split(",")]

print(f"You selected '{choice_map[choice][0]}' for countries: {countries}")

# Plot all countries on one chart
fig, ax = plt.subplots(figsize=(12,6))
for country in countries:
    c = CountryData(country)
    getattr(c, indicator_method_name)(ax=ax)

# Enable clickable legend to toggle lines
make_lines_toggleable(ax)

plt.show()
