import polars as pl
import string
import random


def create_cipher_maps_letters_digits():

    """
    Generate shuffled sequences of lowercase letters, uppercase letters, and digits.

    This function creates and returns three randomly shuffled strings:
    1. All lowercase ASCII letters ('a' to 'z')
    2. All uppercase ASCII letters ('A' to 'Z')
    3. All digits ('0' to '9')

    Returns:
        list[str]: A list containing three strings in the following order:
                   [shuffled_lowercase_letters, shuffled_uppercase_letters, shuffled_digits]

    Example:
        shuffled_data = create_cipher_maps_letters_digits()
        print(shuffled_data)
        # Output: ['qazwsxedcrfvtgbyhnujmikolp', 'ZYXWVUTSRQPONMLKJIHGFEDCBA', '4938571602']
    """

    lower_char_list = list(string.ascii_lowercase)
    random.shuffle(lower_char_list)

    upper_char_list = list(string.ascii_uppercase)
    random.shuffle(upper_char_list)

    num_list = list(string.digits)
    random.shuffle(num_list)
    
    return [
        ''.join(lower_char_list),
        ''.join(upper_char_list),
        ''.join(num_list)
    ]



def mask_columns(df: pl.DataFrame,columns_to_mask: list,letters_lower: str,letters_upper: str,digits_map: str) -> pl.DataFrame:

    """
    Mask specified columns in a Polars DataFrame by replacing characters according to given mapping strings.

    This function processes each column specified in `columns_to_mask` and performs character-level
    substitutions for lowercase letters, uppercase letters, and digits. Rows with NULL, "NA"
    (case-insensitive), or empty strings are preserved without masking.

    Args:
        df (pl.DataFrame): Input Polars DataFrame to mask.
        columns_to_mask (list): List of column names to apply masking.
        letters_lower (str): Mapping string of 26 characters used to substitute lowercase letters (a-z).
        letters_upper (str): Mapping string of 26 characters used to substitute uppercase letters (A-Z).
        digits_map (str): Mapping string of 10 characters used to substitute digits (0-9).

    Returns:
        pl.DataFrame: A new Polars DataFrame with the specified columns masked and other columns unchanged.

    Example:
        masked_df = mask_columns(
            df,
            columns_to_mask=['name', 'id'],
            letters_lower='qazwsxedcrfvtgbyhnujmikolp',
            letters_upper='ZYXWVUTSRQPONMLKJIHGFEDCBA',
            digits_map='4938571602'
        )
    """

    for col in columns_to_mask:
        if col in df.columns:
            # Convert column to UTF8 string and strip whitespace
            s = pl.col(col).cast(pl.Utf8).str.strip_chars()

            # Identify NULL, "NA" (case-insensitive), or empty strings; these will not be masked
            is_na = s.is_null() | s.str.to_uppercase().eq("NA") | s.eq("")

            # Replace lowercase letters a-z according to letters_lower mapping
            for src, tgt in zip(string.ascii_lowercase, letters_lower):
                s = s.str.replace_all(src, tgt)

            # Replace uppercase letters A-Z according to letters_upper mapping
            for src, tgt in zip(string.ascii_uppercase, letters_upper):
                s = s.str.replace_all(src, tgt)

            # Replace digits 0-9 according to digits_map mapping
            for src, tgt in zip('0123456789', digits_map):
                s = s.str.replace_all(src, tgt)

            # Apply mask: preserve original where is_na, otherwise use masked string
            df = df.with_columns(
                pl.when(is_na).then(pl.col(col)).otherwise(s).alias(col)
            )

    return df


def process_maskify(input_file: str,separator: str,columns_to_mask: list,enCipher: tuple,output_file: str,chunk_size: int = 500_000) -> str:
    
    """
    Process a large CSV file in chunks by masking specified columns and writing the result to a new CSV file.

    This function reads the input CSV file in memory-efficient chunks using Polars,
    applies character-level masking to specified columns, and writes the masked data
    to the output file incrementally, avoiding large memory usage.

    Args:
        input_file (str): Path to the input CSV file to process.
        separator (str): Field separator in the input CSV file (e.g., ',' or '|').
        columns_to_mask (list): List of column names to apply masking.
        enCipher (tuple): Tuple containing three mapping strings for masking:
                          (letters_lower_map, letters_upper_map, digits_map).
                          Example: ('zyx...cba', 'ZYX...CBA', '9876543210')
        output_file (str): Path to the output CSV file where masked data will be written.
        chunk_size (int, optional): Number of rows to process per chunk. Default is 500,000.

    Returns:
        str: Path to the output file containing masked data.

    Example:
        output_path = process_maskify(
            input_file='data/input.csv',
            separator=',',
            columns_to_mask=['name', 'id'],
            enCipher=('zyxwvutsrqponmlkjihgfedcba', 'ZYXWVUTSRQPONMLKJIHGFEDCBA', '9876543210'),
            output_file='data/output_masked.csv'
        )
    """

    # Unpack the encryption mappings provided by the caller
    letters_lower, letters_upper, digits_map = enCipher[0], enCipher[1], enCipher[2]

    # Initialize a Polars batched CSV reader for efficient memory usage
    reader = pl.read_csv_batched(
        input_file,
        has_header=True,
        separator=separator,
        batch_size=chunk_size,
        infer_schema_length=0
    )

    first_chunk = True
    batches = reader.next_batches(1)

    # Open the output file in binary write mode
    with open(output_file, "wb") as f_out:
        while batches:
            chunk_df = batches[0]  # Get the current chunk as a DataFrame

            # Mask the specified columns in this data chunk
            masked_chunk = mask_columns(
                chunk_df,
                columns_to_mask,
                letters_lower,
                letters_upper,
                digits_map
            )

            # Write the masked data chunk to output file
            # Only include header in the first chunk
            masked_chunk.write_csv(
                f_out,
                include_header=first_chunk,
                separator=separator
            )

            first_chunk = False  # Disable header for subsequent chunks
            batches = reader.next_batches(1)  # Load next chunk

    return output_file