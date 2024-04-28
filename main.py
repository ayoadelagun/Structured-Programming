import sys
import numpy
import math
import re
import cmath
import csv

##################################################################################################
#ComponentTypeException
##################################################################################################

class ComponentTypeException(Exception):
    def __init__(self):
        # Initialize the Exception base class with a custom message
        super().__init__()

##################################################################################################
#DataExtract
##################################################################################################

class DataExtract:

    """
    Class with argument atribute file_name
    Reads file and breaks down resultant string into sections defined by the delimiters
    Uses regular expressions to store "Value name" = "Vlaue" example ("n1=1" => dict('n1',1))
    repreates for each section handeling errors apropriatly

    :def read_file

        Open and store [file_name] and [content]
        romve comments and break up [content]
        format content so that each line is an elemnt in a list
        process each section, stroing the resukts in apropriate data structures

        INPUT: file_name string
        OUTPUT: formatted_circuit:list(dict(string,float))
                formatted_terms:dict(string,float)
                formatted_output:dict(string,string)

    :def remove_comments

        Take the argument string, iterate trough it and remove lines begining with #
        lines in the string are delimmited by /n
    
        INPUT: text string
        OUTPUT: filtered_text string

    :def parse_section

        Use the delimmiter /n in the string to break
        it down and store each line in a list

        INPUT: [circuit,terms,outupt]_section string
        OUTPUT: [circuit,terms,outupt]_data list:string

    :def node_helper

        Store the data found in the regEx matches identified as nodes

        INPUT: matches list:string
        OUTPUT: node_dict:Dict

    :def value_helper

        Store the data found in the regEx matches identified as type=value
        with added support for prefixes

        INPUT: matches list:string
        OUTPUT: val_dict:Dict
    
    :def process_[circuit,terms,outupt]_section

        Store the data found in the regEx matches in apropriate data structures

        INPUT: [circuit,terms,outupt]_data list:string
        OUTPUT: formatted_[terms,outupt]_data:dict(string,[int,string])
                formatted_circuit_data list:dict(string,float)

    """

    def __init__(self, file_name):
        self.file_name = file_name
        self.conversionDict = {
            'p': 'e-12',
            'n': 'e-9',
            'u': 'e-6',
            'm': 'e-3',
            'k': 'e3',
            'M': 'e6',
            'G': 'e9'
        }
        self.read_file()

    def read_file(self):
        with open(self.file_name, 'r') as file:
            content = file.read()
            # content is the raw text contained in the input file
        Real_Content = self.remove_comments(content)
        # Remove lines that begin with '#'
        try:
            circuit_section = Real_Content.split('<CIRCUIT>')[1].split('</CIRCUIT>')[0]
            terms_section = Real_Content.split('<TERMS>')[1].split('</TERMS>')[0]
            output_section = Real_Content.split('<OUTPUT>')[1].split('</OUTPUT>')[0]
            # Split the content by sections
        except IndexError:
            # This will occur when a delimiter is missing
            # The spec and model files mean that the program must not terminate but an empty file must be exported
            # hence the assignation of sections with empty lists
            print("Missing required input information (Some delimiting text was not found)")
            circuit_section = []
            terms_section = []
            output_section = []
        try:
            # Get each section into the form of a list where each line is stored at an index
            circuit_data = self.parse_section(circuit_section)
            terms_data = self.parse_section(terms_section)
            output_data = self.parse_section(output_section)
            # Process each section using regEx and strore golablly in dic for acces outside of class object
            self.formatted_Circ_Values = self.process_circuit_data(circuit_data)
            self.formatted_Term_Values = self.process_terms_data(terms_data)
            self.formatted_Outputs = self.process_output_data(output_data)
        except Exception:
            # This will occur when any contense within the sections cannot be processed as intended
            # E.g. there is a string ('BREXIT') where a float (3.18e-9) should be
            # The spec and model files mean that the program must not terminate but an empty file must be exported
            # hence the assignation of sections with empty lists
            self.formatted_Circ_Values = [{}]
            self.formatted_Term_Values = {}
            self.formatted_Outputs = {}

    def remove_comments(self, text):
        """
        Remove lines begining with '#'

        >>> extract = DataExtract('b_RC.net')
        >>> extract.remove_comments('Hello\\n#Hello')
        'Hello'
        >>> extract.remove_comments('#Hello\\n#Hello\\nR=50')
        'R=50'
        >>> extract.remove_comments('#L=3.18e-9\\n#C=3.18e-12')
        ''
        """
        # Split the text into lines and filter out those that start with '#'
        lines = text.splitlines()
        filtered_lines = [line for line in lines if not line.lstrip().startswith('#')]
        # Join the filtered lines back into a single string
        return '\n'.join(filtered_lines)
    
    def parse_section(self, section):
        """
        Store each line in the string as an entry in a list

        >>> extract = DataExtract('b_RC.net')
        >>> extract.parse_section('Hello\\nHello')
        ['Hello', 'Hello']
        >>> extract.parse_section('Hello\\nHello\\nR=50')
        ['Hello', 'Hello', 'R=50']
        >>> extract.parse_section('\\n')
        ['']
        """
        data = []
        # Iterate through each line of the text and add the line to the data list
        for line in section.strip().split('\n'):
                data.append(line)
        return data
    

    def node_helper(self, matches):
        node_dict = {}
        for name, value in matches:
            node_dict[name] = int(value)
        return node_dict
    
    def value_helper(self, matches):
        val_dict = {}
        for name, value in matches:
            try: 
            # Store the component value and type and store each of them in the variables dict
                compVal = float(value)
                type = str(name)
                val_dict['type'] = type
                val_dict['value'] = compVal
            except ValueError:
                # Attempt this conversion again using the powers of 10 prefix
                try:
                    count = 0
                    for fix, exp in self.conversionDict.items():
                        if fix in value:
                            count +=1
                            new_value = value + exp
                            new_value = new_value.replace(fix,'')
                            val_dict['value'] = float(new_value)
                            val_dict['type'] = str(name)
                    if count ==0:
                        raise ValueError
                except ValueError:
                    #This will occur if a component has an incompatable type or value
                    print(f"Value for '{name}' is not in supported format: '{value}'")
                    component_data = []
                    return component_data
        return val_dict



    def process_circuit_data(self, circuit_data):
        """
        Store the circuit data in list of dict
        each dict represents one component

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_circuit_data(['n1=1 n2=2 R=50','n1=2 n2=0 C=5e-9'])
        [{'n1': 1, 'n2': 2, 'type': 'R', 'value': 50.0}, {'n1': 2, 'n2': 0, 'type': 'C', 'value': 5e-09}]
        >>> extract.process_circuit_data(['n1=1 n2=2 R=50','n1=2 n2=0 C=error'])
        Value for 'C' is not in supported format: 'error'
        []
        """
        component_data = []
        # Define regular extression that matches the formatting of the input file
        pattern_nodes = r'(\w+)=(\S+)'
        pattern_value = r'(\w+)=(\d+(?:\.\d+)?(?:e[+-]?\d+)?[numkMG]?)'

        # Iterate through each component in the circuit
        # Components can be defined as a line in the circuit section
        for component in circuit_data:
            # Isolate all matches in the component line
            pattern = r'^(.*?)(\s\w+=(?:\d+(?:\.\d+)?(?:e[+-]?\d+)?|[a-zA-Z]+)\s?[numkMG]?)$'
            match = re.search(pattern, component)
            nodes_string = match.group(1)
            value_string = match.group(2).replace(' ','')
            matches_nodes = re.findall(pattern_nodes, nodes_string)
            matches_value = re.findall(pattern_value, value_string)
            if matches_nodes and matches_value:
                # Iterate through each match of the RegEx
                nodes = self.node_helper(matches_nodes)
                val = self.value_helper(matches_value)
                combined_dict = {**nodes, **val}
                component_data.append(combined_dict)
            else:
                #This will occur if a component has an incompatable type or value
                print(f"Value in '{component}' is not in supported format")
                component_data = []
                return component_data
        return component_data

    def process_terms_data(self,terms_data):
        """
        Store the terms data in a dict

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_terms_data(['VT=5 RS=50','RL=50','Fstart=10.0 Fend=10e+6 Nfreqs=50'])
        {'VT': 5, 'RS': 50, 'RL': 50, 'Fstart': 10.0, 'Fend': 10000000.0, 'Nfreqs': 50}
        >>> extract.process_terms_data(['Vth=50','Fstart=10.0 Fend=10e+6 Nfreqs=error'])
        Value for 'Nfreqs' is not in supported format: 'error'
        {}
        """
        # Define regular extression that matches the formatting of the input file
        pattern = r'(\b\w+\b)=(\S+)'
        # Join the section together so we dont need to iterate through each line
        # Remove this later!!!!
        combined_string = ' '.join(terms_data)
        # Isolate all matches in the string
        matches = re.findall(pattern, combined_string)
        variables = {}
        # Iterate through each match of the RegEx
        for name, value in matches:
            try:
                # Try to store match in variables dict as string-int
                variables[name] = int(value)
            except ValueError:
                # This will occur when value cannot be cast to type int
                try:
                    # Try to store match in variables dict as string-float
                    variables[name] = float(value)
                except ValueError:
                    # This will occur when value cannot be cast to type int or folat
                    # This means that an error is present in the input file
                    # The spec and model files mean that the program must not terminate but an empty file must be exported
                    # hence the return of an empty dict
                    print(f"Value for '{name}' is not in supported format: '{value}'")
                    return {}
        return variables
    
    def process_output_data(self,output_data):
        """
        Store the circuit data in list of dict
        each dict represents one component

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_output_data(['Hello hi', 'Farewell bye'])
        {'Hello': 'hi', 'Farewell': 'bye'}
        """
        # Define regular extression that matches the formatting of the input file
        pattern = r'(\w+)\s*(\w+)?'
        # Isolate all matches in the string cast of the section
        matches = re.findall(pattern, str(output_data))
        variables = {}
        # Iterate through matches
        for name, unit in matches:
                # Store match in variables dict as string-string
                variables[name+" "+unit] = str(unit)
        return variables



##################################################################################################
#Impedance
##################################################################################################

class Impedance:

    """
    Class with argument atributes Pin1:int Pin2:int Value:float Type:string
    Calculates and stores atibutes In_node and ABCD
    thease atributes are calclated and assigned on initialization

    :def MAT_GEN

        Identifies if the component being represented is in shunt or series
        uses the generic ABCD matrix to represent individual component

        INPUT: Pin1:int Pin2:int Value:float Type:string
        OUTPUT: ABCD numpy.array

    :def Node_ID

        Identifies which of n1 and n2 (Pin1 Pin2) is the inout node
    
        INPUT: Pin1:int Pin2:int
        OUTPUT: In_node:int

    """

    #Object Represnetin an anolog component in cascade
    def __init__(self, Pin1, Pin2, Value, Type):
        self.Type = Type
        self.Pin1 = Pin1
        self.Pin2 = Pin2
        self.Value = Value
        self.In_node = self.Node_ID()

    def get_Pin1(self):
        return self.Pin1

    def get_Pin2(self):
        return self.Pin2

    def get_Value(self):
        return self.Value

    def MAT_GEN(self, F):
        # Calculate ABCD matrix based on Pin1, Pin2, and Value
        if self.Type == "R":
            if self.Pin1 == 0 or self.Pin2 == 0:
                ABCD = numpy.array([[1, 0], [1/self.Value, 1]])
            else:
                ABCD = numpy.array([[1, self.Value], [0, 1]])
            return ABCD
        elif self.Type == "G":
            if self.Pin1 == 0 or self.Pin2 == 0:
                ABCD = numpy.array([[1, 0], [self.Value, 1]])
            else:
                ABCD = numpy.array([[1, 1/self.Value], [0, 1]])
            return ABCD
        
    def Node_ID(self):
        if self.Type not in ["R", "G"]:
            raise ComponentTypeException()
        if min(self.Pin1,self.Pin2) == 0:
                in_node = max(self.Pin1,self.Pin2)
        else:
                in_node = min(self.Pin1,self.Pin2)
        return in_node


##################################################################################################
#FreqDepImpedence
##################################################################################################

class FreqDepImpedence(Impedance):

    """
    Class with argument atributes Pin1:int Pin2:int Value:float Type:string Freq:list:float
    Calculates and stores atibutes In_node impedence(dict) and ABCD(dict)
    frequencies map to impedences, which can then be used to calculate the ABCD matrix at that frquency
    the impedence atribute is calclated and assigned on initialization but the matricies are not

    :def Z_GEN

        Returns that impedence at all frequencies in [Freq] as a
        dictonary where frequenct mpas to impedence

        INPUT: Value:float Freq:list:float
        OUTPUT: Impedences:dict(float,float)

    :def MAT_GEN

        Identifies if the component being represented is in shunt or series
        uses the generic ABCD matrix to represent individual component at any 
        given frequency by accessing the Impedences dictonary. This will not be called in the __innit__
        and will be accesable outside the class

        INPUT: Pin1:int Pin2:int Value:float Type:string Frequency:float
        OUTPUT: ABCD:dict(float,float)

    :def Node_ID

        Identifies which of n1 and n2 (Pin1 Pin2) is the inout node
    
        INPUT: Pin1:int Pin2:int
        OUTPUT: In_node:int

    """

    def __init__(self, Pin1, Pin2, Value, Type, Freq):
        super().__init__(Pin1, Pin2, Value, Type)
        self.Type = Type
        self.Freq = Freq
        self.In_node = self.Node_ID()
        self.Z = self.Z_GEN()

    def get_Type(self):
        return self.Type

    def Z_GEN(self):
        #Method for genrating an impedence (Z) value frequency in rnage of frequency
        #Output is a lookup table of impedences with the range Freq
        Z = {}
        if self.Type == "C":
            for F in self.Freq:
                Z[F] = (1/(1j*2*math.pi*F*self.Value))
        elif self.Type == "L":
            for F in self.Freq:
                Z[F] = (1j*2*math.pi*F*self.Value)
        return Z

    def MAT_GEN(self, F):
    #Method for generating ABCD parameter matrices
        ABCD = []
        if self.Pin1 == 0 or self.Pin2 == 0:
             ABCD = numpy.array([[1, 0], [1/self.Z[F], 1]])
        else:
               ABCD = numpy.array([[1, self.Z[F]], [0, 1]])
        return ABCD
    
    def Node_ID(self):
        if min(self.Pin1,self.Pin2) == 0:
                in_node = max(self.Pin1,self.Pin2)
        else:
                in_node = min(self.Pin1,self.Pin2)
        return in_node


##################################################################################################
#Circ
##################################################################################################

class Circ:

    """
    Class with argument atributes components_list:list(component) Freq:list(float) LoadRes:int Vth:int Rs:int
    Order the list of components
    Calculates casacde netwrok ABCD matrix for the circuit defined by the list of components 
    uses this matrix and the other arguments to calulate V1:folat V2:float I1:float I2:float
    Zin:float Zout:float Pin:float Pout:float Ai:float Av:float on init

    :def Order_components

        Returns the ordered componets list by the In_node key

        INPUT: components_list:list(component)
        OUTPUT: components_list_ordered:list(component)

    :def Vin_calc, Iin_calc

        Uses the class argument atributes to calculate the input measurments

        INPUT: Vth:float Rs:float Zin:dict(float,float)
        OUTPUT: ABCD:dict(float,float)

    :def Z_GEN   

        Uses the class argument atributes and the calculated matrix dictonary
        to calculate the impedence of the network

        INPUT: LoadRes:int Rs:int Cascade_ABCD_MAT:dict(float,numpy.array)
        OUTPUT: Zin:dict(float,float) Zout:dict(float,float)

    :def MAT_GEN

        For each frequency in Freq cascade the component ABCD matricies and store
        in a dictonary where frequency maps to a cascade matrix

        INPUT: Freq:list(float) components_list:list(component) 
        OUTPUT: Cascade_ABCD_MAT:dict(float,numpy.array)

    // Calcuate the rest of the required outputs uing this matrix

    :def get_Ordered_Outputs

        Convert calculated atributes to dB if specified in the outputs section of the text file
        do this by accessing the order argument which is dict(Vlaue type e.g. 'Vin' , measurment e.g. dBV)
        return a dictoanry where Value types map to the calculated values

        INPUT: [All calculated outputs]
        OUTPUT: Outputs:dict(string,float)

    """

    def __init__(self, components_list, Freq, LoadRes, Vth, Rs):
        self.components_list = components_list
        self.Freq = Freq
        self.LoadRes = LoadRes
        self.Vth = Vth
        self.Rs = Rs
        self.components_list_Ordored = self.Order_components()
        self.cascade_ABDC_mat = self.MAT_GEN()

        self.Zin, self.Zout = self.Z_GEN()
        self.Vin = self.Vin_CALC()
        self.Iin = self.Iin_CALC()
        self.Vout, self.Iout = self.calculate_VoutIout()
        self.Pin = self.Pin_CALC()
        self.Pout = self.Pout_CALC()
        self.Av = self.Av_CALC()
        self.Ai = self.Ai_CALC()
        self.Ap = self.Ap_CALC()
        

    def Order_components(self):
        return sorted(self.components_list, key=lambda x: (x.In_node, not (x.Pin1 == 0 or x.Pin2 == 0)))
            
    def MAT_GEN(self):
        MAT = {}
        for F in self.Freq:
            current_MAT = numpy.array([[1,0],[0,1]])
            for component in self.components_list_Ordored:
                ABCD = component.MAT_GEN(F)
                current_MAT = current_MAT @ ABCD
            MAT[F] = current_MAT
        return MAT
    
    def Vin_CALC(self):
        V1 = {}
        for F in self.Freq:
            V1[F] = self.Vth * (self.Zin[F]/(self.Zin[F] + self.Rs))
        return V1
    
    def Iin_CALC(self):
        I1 = {}
        for F in self.Freq:
            I1[F] = self.Vin[F]/self.Zin[F]
        return I1
    
    def Pin_CALC(self):
        Pout = {}
        for F in self.Freq:
            V1 = self.Vin[F]
            I1 = self.Iin[F]
            Pout[F] = V1 * I1.conjugate()
        return Pout
    
    def Pout_CALC(self):
        Pin = {}
        for F in self.Freq:
            V2 = self.Vout[F]
            I2 = self.Iout[F]
            Pin[F] = V2 * I2.conjugate()
        return Pin
    
    def Av_CALC(self):
        Av = {}
        for F in self.Freq:
            A, B = self.cascade_ABDC_mat[F][0, 0], self.cascade_ABDC_mat[F][0, 1]
            Z_L = self.LoadRes
            Av[F] = 1 / (A + B / Z_L)
        return Av

    def Ai_CALC(self):
        Ai = {}
        for F in self.Freq:
            Ai[F] = self.Iout[F]/self.Iin[F]
        return Ai
    
    def Ap_CALC(self):
        Ap = {}
        for F in self.Freq:
            Ap[F] = self.Pout[F]/self.Pin[F]
        return Ap

    
    def Z_GEN(self):
        Zin = {}
        Zout = {}
        for F in self.Freq:
            A, B, C, D = self.cascade_ABDC_mat[F][0, 0], self.cascade_ABDC_mat[F][0, 1], self.cascade_ABDC_mat[F][1, 0], self.cascade_ABDC_mat[F][1, 1]
            Z_L = self.LoadRes
            Z_S = self.Rs
            Zin[F] = (A * Z_L + B) / (C * Z_L + D)
            Zout[F] = (D * Z_S + B) / (C * Z_S + A)
        return Zin, Zout
    
    def calculate_VoutIout(self):
        V2 = {}
        I2 = {}
        for F in self.Freq:
            ABCD = self.cascade_ABDC_mat[F]
            A, B, C, D = ABCD[0, 0], ABCD[0, 1], ABCD[1, 0], ABCD[1, 1] #correct
            V1 = self.Vin[F] #correct
            I1 = self.Iin[F] #correct
            #det = numpy.complex128(A * D - B * C)
            #Vout =  numpy.complex128((D * V1 - B * I1) / det)
            Iout = V1/(A*self.LoadRes+B)
            Vout = self.LoadRes * Iout
            V2[F], I2[F] = Vout, Iout
        return V2, I2
    
    def get_Ordered_Outputs(self, order):
        Outputs = {}
        phases_rad = []  # Collect phases for debugging

        for F in self.Freq:
            Inter = {}
            for param, unit in order.items():
                parts = param.split(" ")
                param_raw = parts[0]
                value = getattr(self, param_raw, None)
                if value is None:
                    continue  # Skip if attribute does not exist
                if 'dB' in unit:
                    # Define dB_multiplier based on the presence of specific keywords in param
                    if any(keyword in param for keyword in ['Pout', 'Pin', 'Zin', 'Zout', 'Ap']):
                        dB_multiplier = 10
                    else:
                        dB_multiplier = 20
                    mag_dB = dB_multiplier * math.log10(abs(value[F])) if abs(value[F]) > 0 else -float('inf')
                    phase_rad = cmath.phase(value[F])  # Keep phase in radians
                    phases_rad.append(phase_rad)  # Collect phase for debugging
                    Inter[param] = {'Mag': mag_dB, 'Phase': phase_rad}
                else:
                    Inter[param] = value[F]
            Outputs[F] = Inter

        return Outputs


##################################################################################################
#CircResultsExporter
##################################################################################################

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



##################################################################################################
#Main
##################################################################################################


def errorexporter(file_path):
    with open(file_path, 'w', newline='') as output_file:
            output_file.write() 

# Usage


if len(sys.argv) != 3:
    print("Usage: python MyProg.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
Txt_Data = DataExtract(input_file)
try:
    try:
        freq = numpy.linspace(Txt_Data.formatted_Term_Values['Fstart'], Txt_Data.formatted_Term_Values['Fend'], Txt_Data.formatted_Term_Values['Nfreqs'])
    except Exception:
        freq = numpy.logspace(numpy.log10(Txt_Data.formatted_Term_Values['LFstart']), numpy.log10(Txt_Data.formatted_Term_Values['LFend']), Txt_Data.formatted_Term_Values['Nfreqs'])
except Exception:
    errorexporter(output_file)

frequencies = freq

components = []
for component_data in Txt_Data.formatted_Circ_Values:
    try:
        comp = Impedance(
            Pin1=component_data['n1'], 
            Pin2=component_data['n2'], 
            Value=component_data['value'], 
            Type=component_data['type']
        )
    except ComponentTypeException:
        comp = FreqDepImpedence(
            Pin1=component_data['n1'], 
            Pin2=component_data['n2'], 
            Value=component_data['value'], 
            Type=component_data['type'], 
            Freq=frequencies
        )
    components.append(comp)

if len(components) != 0:
    circuit = Circ(components_list= components, Freq= frequencies, LoadRes= Txt_Data.formatted_Term_Values['RL'], Vth= Txt_Data.formatted_Term_Values['VT'], Rs= Txt_Data.formatted_Term_Values['RS'])
    param = Txt_Data.formatted_Outputs
    x = circuit.get_Ordered_Outputs(param)
    exporter = CircResultsExporter(circuit, param)
    exporter.export_to_csv(output_file)
else:
    errorexporter(output_file)
