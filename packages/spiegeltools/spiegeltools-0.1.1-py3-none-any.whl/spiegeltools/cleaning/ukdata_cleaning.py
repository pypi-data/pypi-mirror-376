import polars as pl
import os, glob


def merge_csv_files(input_folder: str, output_file: str) -> Tuple[pl.DataFrame, TextIO]:
    """Merge all CSV files in the input folder into a single DataFrame and save it to the output file.
    Args:
        input_folder (str): Path to the folder containing CSV files.
        output_file (str): Path to the output CSV file.
    Returns:
        Tuple[pl.DataFrame, TextIO]: Merged DataFrame and a file object for the output file.
    """
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))
    df_list = [pl.read_csv(file) for file in csv_files]
    df = pl.concat(df_list)
    df.write_parquet(output_file)
def set_location(df: pl.DataFrame, country: str, city: str, capital: bool, year: int) -> pl.DataFrame:
    """Set date and location information in the DataFrame.
    Args:
        df (pl.DataFrame): DataFrame to modify.
        country (str): Country name.
        city (str): City name.
        capital (bool): Whether the city is a capital.
        year (int): Year of the data.
    Returns:
        pl.DataFrame: Modified DataFrame with location and date information.
    """
    df = df.with_columns([
        pl.lit(country).alias("Country"),
        pl.lit(city).alias("City"),
        pl.lit(capital).alias("Capital"),
        pl.lit(year).alias("Year")
    ])
    return df
def split_month_year(df: pl.DataFrame) -> pl.DataFrame:
    try:
        df = df.with_columns(
        pl.col("Month")
        .str.split("-")
        .list.get(1)
        .cast(pl.Int8)
        .alias("Month")
        )
    except Exception as e:
        print("This function only supports UK Crime Datasets.")
    return df
def compare_dataframes(df1: pl.DataFrame) -> str:
    """Compare the columns of the DataFrame with a standard DataFrame.
    Args:
        df1 (pl.DataFrame): DataFrame to compare.
    Returns:
        str: Message indicating if the DataFrame matches the standard structure.
    """
    standard_df = pl.DataFrame({
        "Year": ["Hey, You"],
        "Month": ["Out there on your own"],
        "Country": ["Sitting naked by the phone"],
        "City": ["Would you touch me?"],
        "Capital": ["Hey, you"],
        "Crime Type": ["Don't tell me there's no hope at all"],
        "Outcome": ["Together we stand, divided we fall"],
    })
    # Yeah this is a Pink Floyd song, but it fits the context of checking DataFrame columns.
    for col in [c.lower() for c in standard_df.columns]:
        if col not in [c.lower() for c in df1.columns]:
            print(f"Column '{col}' is missing in the DataFrame.")

    for col in [c.lower() for c in df1.columns]:
        if col not in [c.lower() for c in standard_df.columns]:
            print(f"Column '{col}' is not very important. Delete it if you want.")