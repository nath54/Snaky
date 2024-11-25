def hex_to_rgba(hex_code):
    # Remove the hash symbol if present
    hex_code = hex_code.lstrip('#')

    # Convert the hex values to RGB integers
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)

    # RGBA with default alpha = 255 (fully opaque)
    return r, g, b, 255

def process_file(input_file, output_file="tmp.txt"):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # Strip any extra whitespace/newlines
            hex_code = line.strip()

            if hex_code:  # Make sure the line is not empty
                rgba = hex_to_rgba(hex_code)

                # Format the output: hex code with the corresponding RGBA values
                formatted_output = f"{hex_code:9}    ( {rgba[0]:3}, {rgba[1]:3}, {rgba[2]:3}, {rgba[3]:3})\n"

                # Write to output file
                outfile.write(formatted_output)

# Example usage
input_file = "colors.txt"  # Replace this with your input file path
process_file(input_file)
