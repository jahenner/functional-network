import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys
import os
import io
import base64
import tkinter as tk
from PIL import Image, ImageTk

def display_image_from_output(output):
    if 'data' in output and 'image/png' in output['data']:
        image_data = base64.b64decode(output['data']['image/png'])
        image = Image.open(io.BytesIO(image_data))
        root = tk.Tk()
        img = ImageTk.PhotoImage(image)
        panel = tk.Label(root, image=img)
        panel.pack(side="bottom", fill="both", expand="yes")
        root.mainloop()
    elif 'data' in output and 'image/jpeg' in output['data']:
        # Similar logic for JPEG
        image_data = base64.b64decode(output['data']['image/jpeg'])
        image = Image.open(io.BytesIO(image_data))
        root = tk.Tk()
        img = ImageTk.PhotoImage(image)
        panel = tk.Label(root, image=img)
        panel.pack(side="bottom", fill="both", expand="yes")
        root.mainloop()
    else:
        print("Output does not contain PNG or JPEG image data.")


def print_notebook_cells(notebook_path):
    """
    Prints the contents of each cell in a Jupyter Notebook, along with its index.

    Args:
        notebook_path (str): The fully-qualified path to the Jupyter Notebook file.
    """
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}", file=sys.stderr)
        return

    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        print(f"Error reading notebook: {e}", file=sys.stderr)
        return

    for index, cell in enumerate(nb.cells):
        print(f"--- Cell Index: {index} ---")
        if cell.cell_type == 'code':
            print("Cell Type: Code")
            print("Source:")
            for line in cell.source.splitlines():
                print(f"  {line}")
        elif cell.cell_type == 'markdown':
            print("Cell Type: Markdown")
            print("Source:")
            for line in cell.source.splitlines():
                print(f"  {line}")
        elif cell.cell_type == 'raw':
            print("Cell Type: Raw")
            print("Source:")
            for line in cell.source.splitlines():
                print(f"  {line}")
        print("-" * 20)


def parse_cell_selection(cell_selection_str):
    """
    Parses a string containing cell selections (ranges and individual indices).

    Args:
        cell_selection_str (str): A string like "1-5,7,9-12".

    Returns:
        list: A sorted list of unique cell indices.
    """
    indices = set()
    parts = cell_selection_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                indices.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid range format: {part}")
        else:
            try:
                indices.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid index: {part}")
    return sorted(list(indices))

def run_jupyter_selected_cells(notebook_path, cell_selection_str):
    """
    Executes a selection of cells (ranges and/or specific indices)
    in a Jupyter Notebook and prints the output of the last executed cell.

    Args:
        notebook_path (str): The fully-qualified path to the Jupyter Notebook file.
        cell_selection_str (str): A string specifying cells to run (e.g., "1-3,5,8-10").
    """
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}", file=sys.stderr)
        return

    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        print(f"Error reading notebook: {e}", file=sys.stderr)
        return

    try:
        cell_indices_to_run = parse_cell_selection(cell_selection_str)
    except ValueError as e:
        print(f"Error parsing cell selection: {e}", file=sys.stderr)
        return

    invalid_indices = [i for i in cell_indices_to_run if not (0 <= i < len(nb.cells))]
    if invalid_indices:
        print(f"Error: Invalid cell indices: {invalid_indices}. Notebook has {len(nb.cells)} cells.", file=sys.stderr)
        return

    # Create a new notebook containing only the selected cells in their original order
    selected_cells = [nb.cells[i] for i in cell_indices_to_run]
    selected_nb = nbformat.v4.new_notebook(cells=selected_cells)

    try:
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3') # Adjust timeout as needed
        ep.preprocess(selected_nb, {'metadata': {'path': os.path.dirname(os.path.abspath(notebook_path))}})

        # Print the output of the *last* executed cell
        if selected_nb.cells:
            last_cell = selected_nb.cells[-1]
            original_last_index = cell_indices_to_run[-1]
            if last_cell.cell_type == 'code' and 'outputs' in last_cell:
                print(f"\nOutput of Cell {original_last_index}:")
                for output in last_cell['outputs']:
                    if output.output_type == 'stream' and output.name == 'stdout':
                        print(output.text)
                    elif output.output_type == 'display_data' and 'image/png' in output.data:
                        print("Cell Output (Image):")
                        display_image_from_output(output)
                    elif output.output_type == 'execute_result' and 'data' in output and 'text/plain' in output.data:
                        print("Cell Output (Result):")
                        print(output.data['text/plain'])

    except Exception as e:
        print(f"Error executing cells: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script_name.py <notebook_path> <cell_selection>", file=sys.stderr)
        print("       <notebook_path>: Fully-qualified path to the Jupyter Notebook.")
        print("       <cell_selection>: A string specifying cells to run (e.g., \"1-3,5,8-10\").")
        sys.exit(1)

    notebook_file = sys.argv[1]
    cell_selection_str = sys.argv[2]

    notebook_file_abspath = os.path.abspath(notebook_file)
    # print_notebook_cells(notebook_file_abspath)
    # sys.exit(0)
    run_jupyter_selected_cells(notebook_file_abspath, cell_selection_str)