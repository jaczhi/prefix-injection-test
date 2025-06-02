import argparse
import ndn.app_support.light_versec
import sys

def process_files(input_file_path, output_file_path):
    try:
        with open(input_file_path, "r") as infile:
            lvs_text = infile.read()

        lvs_model = ndn.app_support.light_versec.compile_lvs(lvs_text)

        with open(output_file_path, "wb") as outfile:
            outfile.write(lvs_model.encode())

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Process an LVS file and output a TLV file.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python your_script_name.py --input ./schema/insert.lvs --output ./schema/insert.tlv
  python your_script_name.py -i input.lvs -o output.tlv
  python your_script_name.py (this will run in interactive mode)
"""
    )
    parser.add_argument(
        "-i", "--input",
        dest="input_file",
        help="Path to the input LVS file (e.g., ./schema/insert.lvs)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="Path for the output TLV file (e.g., ./schema/insert.tlv)"
    )

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file

    if not input_file and not output_file and not any(sys_arg in ['-h', '--help'] for sys_arg in sys.argv):
        # Only print prompt if no args AND not asking for help
        print("Running in interactive mode.")

    if not input_file:
        # Check again, even if interactive mode was announced, to allow one arg to be specified
        # and only prompt for the missing one.
        # Also, only prompt if not asking for help.
        if not any(sys_arg in ['-h', '--help'] for sys_arg in sys.argv):
             input_file = input("Please enter the path to the input LVS file: ")
        elif not args.input_file and not args.output_file: # if no args at all and -h
             parser.print_help()
             return


    if not output_file:
        if not any(sys_arg in ['-h', '--help'] for sys_arg in sys.argv):
            output_file = input("Please enter the path for the output TLV file: ")
        elif not args.input_file and not args.output_file: # if no args at all and -h
            # Help already printed or will be by argparse, so just return if only one was missing
            # and help wasn't explicitly invoked for missing both.
            if args.input_file: # only output was missing and help was called
                 return # avoid double help print
            # if both were missing, help is already handled by the input_file block


    if input_file and output_file:
        process_files(input_file, output_file)
    elif not any(sys_arg in ['-h', '--help'] for sys_arg in sys.argv):
        # Only print error if not asking for help and files are still missing
        print("Both input and output file paths are required. Exiting.")


if __name__ == "__main__":
    main()
