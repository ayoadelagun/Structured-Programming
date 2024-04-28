# This module takes the solved values and outputs them to the specified CSV file. Exports to CSV 

##############################################################################################################################################
#   Filename:       CircResultsExporter.py - Output_Data_CSV.py
#   Summary:        Acceses the calculated results of a circuit and format and export them accoring to spec.
#   Description:    This file contains the CircResultsExporter class which takes as argument a circuit instance and ordered output peramiters.
#                   The main method is export_to_csv which takes as argument the file path where ther output is to be saved.
#                   This method first formats the headers of the output table and then populates it with the calculated values
#                   scaled by prefixes if present,
#                   whilst all values are alligned by the comma at the enbd of the variable.
#                   Docstrings at the start of helper functions contain doctests.
#                   Support for both dB and linear displays is now active!
#
#                   This version of the class supports multiple of the same mesurmewnt to be displayed!
#
#   Version:        v3.04
#   Date:           19/04/2024
#   Authors:        Joshua O Poole
##############################################################################################################################################


class CircResultsExporter:

    """
    Class with argument atributes as the instace of the circuit in question and
    the list of ordered perameters

    :def to_standard_form

        Converts argument into standard form string representation

        INPUT: x:float
        OUTPUT: x:string

    :def export_to_csv

        Colate all of the circuit information and format
        ready to be exported to a csv file
    
        INPUT: File_path:string circuit_instance:circuit
        OUTPUT: N/A

    """

    def __init__(self, circuit_instance, ordered_parameters):
        self.circuit = circuit_instance
        self.ordered_parameters = ordered_parameters
        self.conversionDict = {
            'p': 'e-12',
            'n': 'e-9',
            'u': 'e-6',
            'm': 'e-3',
            'k': 'e3',
            'M': 'e6',
            'G': 'e9'
        }

    def format_number(self, number):
        """
        Format the number into scientific notation with 4 sf.

        >>> exporter = CircResultsExporter(None, None)
        >>> exporter.format_number(113498.765)
        ' 1.135e+05'
        >>> exporter.format_number(-0.04573)
        '-4.573e-02'
        """
        # Check if the number is negative, to adjust the padding correctly
        sign = '-' if number < 0 else ' '
        # Format the number with 4 significant figures
        formatted = f"{sign}{abs(number):.3e}"
        return formatted


    def pad_left_to_comma(self, text, total_length = 10):
        
        """
        add space the text so that the comma ends at the total_length position

        >>> exporter = CircResultsExporter(None, None)
        >>> exporter.pad_left_to_comma('Hello')
        '     Hello'
        >>> exporter.pad_left_to_comma(' 1.135e+05')
        ' 1.135e+05'
        >>> exporter.pad_left_to_comma('Freq')
        '      Freq'
        """
        return ' ' * (total_length - len(text)) + text 

    def export_to_csv(self, file_path):
        # get the ordered outputs from circuit
        ordered_data = self.circuit.get_Ordered_Outputs(self.ordered_parameters)
        
        # Initialize headers and units with padding
        header_row = [self.pad_left_to_comma('Freq')]
        unit_row = [self.pad_left_to_comma('Hz')]

        # Process each parameter-unit pair, pad and add to its assigned row
        # If no unit is present than the parameter is a gain and should be noted 'L'
        # Do dB conversion if needed

        # Iterate through each perameter dinfined by the input .net file
        for param, unit in self.ordered_parameters.items():
            # If the unit is empty the use 'L' as it is a gain
            unit = 'L' if not unit else unit
            parts = param.split(" ")
            peram_raw = parts[0]
            # If dB is present in the unit convert to dB
            if 'dB' in unit:
                # Pad left each item converted into its dB form and extend to the row
                header_row.extend([self.pad_left_to_comma(f'|{peram_raw}|'), self.pad_left_to_comma(f'/_{peram_raw}')])
                unit_row.extend([self.pad_left_to_comma(unit), self.pad_left_to_comma('Rads')])
            else:
                # Pad left each item and extend to the row
                header_row.extend([self.pad_left_to_comma(f'Re({peram_raw})'), self.pad_left_to_comma(f'Im({peram_raw})')])
                unit_row.extend([self.pad_left_to_comma(unit), self.pad_left_to_comma(unit)])


        # Add commas to elements, except for the last entry for both rows
        header_row = [self.pad_left_to_comma(text) + ',' if i < len(header_row) - 1 else self.pad_left_to_comma(text) for i, text in enumerate(header_row)]
        unit_row = [self.pad_left_to_comma(text) + ',' if i < len(unit_row) - 1 else self.pad_left_to_comma(text) for i, text in enumerate(unit_row)]


        # Initialize 2D array with header and unit rows
        # This will be populated with the circuit simulation results
        To2Darray = [header_row, unit_row]

        # Populate the 2D array with data for each frequency
        # Pad and format each entry to a 4sf standard form string
        # Do dB conversion if needed

        # Iterate through each frequency 
        for F in self.circuit.Freq:
            # Intilialize the row and add the padded and fromatted frequecny to it
            row = [self.pad_left_to_comma(self.format_number(F))]
            # Iterate through each ordered paeramiters value at the frequecny F
            for param, unit in self.ordered_parameters.items():
                # Retrive the value from the circuit class instance
                data_point = ordered_data[F][param]
                # handel dB converstion, pad, format and add values to the row
                if 'dB' in unit:
                    dB_removed = unit.replace("dB", "")
                    # In case where dB in unit check for power of 10 prefix in unit
                    if any(unit.startswith(key) for key in self.conversionDict):
                        for key in self.conversionDict.keys():
                            if dB_removed.startswith(key):
                                row.extend([self.pad_left_to_comma(self.format_number(data_point['Mag']/float('1'+self.conversionDict[key]))), 
        # Store Mag scaled by prefix and phase
                                                self.pad_left_to_comma(self.format_number(data_point['Phase']))])
                    else:
                        row.extend([self.pad_left_to_comma(self.format_number(data_point['Mag'])), 
                                    self.pad_left_to_comma(self.format_number(data_point['Phase']))])
                else:
                    if any(unit.startswith(key) for key in self.conversionDict):
                    # Iterate through possable prefixes to find the match
                        for key in self.conversionDict.keys():
                            if unit.startswith(key):
                                    # Store Real and Imaginary parts scaled by prefix
                                    row.extend([self.pad_left_to_comma(self.format_number(data_point.real/float('1'+self.conversionDict[key]))), 
                                                self.pad_left_to_comma(self.format_number(data_point.imag/float('1'+self.conversionDict[key])))])
                    else:
                                row.extend([self.pad_left_to_comma(self.format_number(data_point.real)), 
                                            self.pad_left_to_comma(self.format_number(data_point.imag))])
                    
            
            # Append commas at the end of each data entry, including for the last one
            row_with_commas = [f"{entry}," for entry in row]
            # Append each row the the To2Darray list
            To2Darray.append(row_with_commas)

        # Write the formatted 2D array to a CSV file manually
        with open(file_path, 'w', newline='') as Output_file:
            for row in To2Darray:
                # Combine all the entries in a row into a single string
                line = ' '.join(row)
                # Write the line to the file and add a newline
                Output_file.write(line + '\n')  

        print(f'CSV file has been saved to {file_path}')

if __name__ == "__main__":
    import doctest
    doctest.testmod()
