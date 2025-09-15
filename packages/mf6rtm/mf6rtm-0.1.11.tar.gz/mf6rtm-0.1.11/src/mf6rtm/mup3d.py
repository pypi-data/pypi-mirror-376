"""The mup3d module provides a wrapper for PHRREQC Inputs.
"""

from pathlib import Path
import os
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
from typing import Union
import pandas as pd
import numpy as np
import phreeqcrm
from mf6rtm.solver import solve, DT_FMT, time_units_dict
from mf6rtm import utils
from mf6rtm.config import MF6RTMConfig
from phreeqcrm import yamlphreeqcrm
import yaml


class Block:
    """Base class for PHREEQC input "keyword data blocks".

    Attributes
    ----------
    data : dict
        Dictionary of geochemical components (keys) and their total concentrations
        (list) indexed by block number, similar to a .pqi file.
    names : list
        List of names of geochemical components that serve as keys to the data.
    ic : array
        Initial condition.
    eq_solutions : list
        List of equilibrium solutions.
    options : list
        List of options.
    """
    def __init__(
        self,
        data: dict,
        ic: Union[int, float, np.ndarray, None] = None,
    ) -> None:
        """Initialize a Block instance with inputs from a PHREEQC data block.

        Parameters
        ----------
        data
            PHREEQC components (keys) and their total concentrations (list) indexed by
            block number, similar to a .pqi file.
        ic, optional
            Initial condition concentrations. Default is None.
        """
        self.data = data
        self.names = [key for key in data.keys()]
        self.ic = ic  #: None means no initial condition (-1)
        self.eq_solutions = []
        self.options = []

    def set_ic(self, ic: Union[int, float, np.ndarray]):
        '''Set the initial condition for the block.
        '''
        assert isinstance(ic, (int, float, np.ndarray)), 'ic must be an int, float or ndarray'
        self.ic = ic

    def set_equilibrate_solutions(self, eq_solutions):
        '''Set the equilibrium solutions for the exchange phases.
        Array where index is the exchange phase number and value is the solution number to equilibrate with.
        '''
        self.eq_solutions = eq_solutions

    def set_options(self, options):
        self.options = options


class GasPhase(Block):
    def __init__(self, data) -> None:
        super().__init__(data)


class Solutions(Block):
    """The Solutions Block."""
    def __init__(self, data) -> None:
        super().__init__(data)


class EquilibriumPhases(Block):
    def __init__(self, data) -> None:
        super().__init__(data)


class ExchangePhases(Block):
    def __init__(self, data) -> None:
        super().__init__(data)


class KineticPhases(Block):
    def __init__(self, data) -> None:
        super().__init__(data)
        self.parameters = None

    def set_parameters(self, parameters):
        self.parameters = parameters


class Surfaces(Block):
    def __init__(self, data) -> None:
        super().__init__(data)
        # super().__init__(ic)


class ChemStress():
    def __init__(self, packnme) -> None:
        self.packnme = packnme
        self.sol_spd = None
        self.packtype = None

    def set_spd(self, sol_spd):
        self.sol_spd = sol_spd

    def set_packtype(self, packtype):
        self.packtype = packtype


phase_types = {
    'KineticPhases': KineticPhases,
    'ExchangePhases': ExchangePhases, # TODO: Exchange has to be abstracted to be used with this methods
    'EquilibriumPhases': EquilibriumPhases,
    'Surfaces': Surfaces,
}


class Mup3d(object):
    """The Mup3d class wrapper and extension for a PhreeqcRM model class.

    This class extends the PhreeqcRM class to include additional methods
    that facilitate the coupling to Modflow6 via ModflowAPI.

    Attributes
    ----------
    name : str
        Name of the model.
    wd : str
        Working directory path.
    charge_offset : float
        Charge offset, initialized to 0.0.
    database : str
        Path to the PHREEQC database file.
    solutions : Solutions
        Solutions instance containing the geochemical data.
    init_temp : float, optional
        Initial temperature. Default is 25.0.
    equilibrium_phases : EquilibriumPhases
        Equilibrium phases in the model.
    kinetic_phases : KineticPhases
        Kinetic phases in the model.
    exchange_phases : ExchangePhases
        Exchange phases in the model.
    surfaces_phases : Surfaces
        Surface phases in the model.
    postfix : str
        Postfix for the output files.
    phreeqc_rm : object
        PHREEQC reactive transport model instance.
    sconc : dict[str, np.ndarray]
        Dictionary of concentrations in units of moles per m^3 and structured to
        match the shape of Modflow's grid.
    phinp : object
        PHREEQC input instance.
    components : list
        List of chemical components.
    fixed_components : list
        List of fixed components.
    nlay : int
        Number of layers in the model grid.
    nrow : int
        Number of rows in the model grid.
    ncol : int
        Number of columns in the model grid.
    nxyz : int
        Total number of cells in the model grid, either
        (nlay * nrow * ncol) if DIS or
        (nlay * ncpl) if DISV or
        (nxyz) if DISU.
    grid_shape : tuple
        Shape of the model grid, either
        (nlay, nrow, ncol) if DIS or
        (nlay, ncpl) if DISV or
        (nxyz) if DISU.
    """
    def __init__(
        self,
        name: Union[int, None] = None,
        solutions: Union[Solutions, None] = None,
        nlay: Union[int, None] = None,
        nrow: Union[int, None] = None,
        ncol: Union[int, None] = None,
        ncpl: Union[int, None] = None,
        nxyz: Union[int, None] = None,
        componenth2o: Union[bool, None] = None
    ):
        """Initializes a Mup3d instance with the given parameters.

        Parameters
        ----------
        name : str, optional
            The name of the model. Default is None.
        solutions : Solutions, optional
            Instance of the Solutions class containing the geochemical data.
            Required if name is not an instance of Solutions.
        nlay : int, optional
            Number of layers in the model, if it has a layered grid
            discretization (DIS or DISV).
        nrow : int, optional
            Number of rows in the model, if it has a structured rectangular
            layered grid discretization (DIS).
        ncol : int, optional
            Number of columns in the model, if it has a structured rectangular
            layered grid discretization (DIS).
        ncpl : int, optional
            Number of cells per layer in the model, if it has an unstructured
            layered grid Discretization by Vertices (DISV).
        nxyz : int, optional
            Total number of cells in the model grid, either
            (nlay * nrow * ncol) if DIS or
            (nlay * ncpl) if DISV or
            (nxyz) if DISU.

        Raises
        ------
        ValueError
            If solutions is not provided.
        ValueError
            If any of nlay, nrow, or ncol is not provided.
        """
        if solutions is None and isinstance(name, Solutions):
            # New style: first argument is solutions
            solutions = name
            name = None
        # Validate required parameters
        if solutions is None:
            raise ValueError("solutions parameter is required")
        if (any(param is None for param in [nlay, nrow, ncol]) and
            any(param is None for param in [nlay, ncpl])):
            raise ValueError(("nlay, nrow, and ncol parameters are required "
                " for DIS, or nlay and ncpl parameters are required for DISV"))
        self.name = name
        self.wd = None
        self.charge_offset = 0.0
        self.database = os.path.join('database', 'pht3d_datab.dat')
        self.solutions = solutions
        self.init_temp = 25.0
        self.equilibrium_phases = None
        self.kinetic_phases = None
        self.exchange_phases = None
        self.surfaces_phases = None
        self.postfix = None
        # self.gas_phase = None
        # self.solid_solutions = None
        self.phreeqc_rm = None
        self.sconc = None
        self.phinp = None
        self.components = None
        self.fixed_components = None
        self.componenth2o = False
        self.config = MF6RTMConfig() #default config

        # Set grid parameters for DIS
        if all(param is not None for param in [nlay, nrow, ncol]):
            self.nlay = int(nlay)
            self.nrow = int(nrow)
            self.ncol = int(ncol)
            self.nxyz = self.nlay * self.nrow * self.ncol
            self.grid_shape = (self.nlay, self.nrow, self.ncol)
        # Set grid parameters for DISV
        elif all(param is not None for param in [nlay, ncpl]):
            self.nlay = int(nlay)
            self.ncpl = int(ncpl)
            self.nxyz = self.nlay * self.ncpl
            self.grid_shape = (self.nlay, self.ncpl)
        # Set grid parameters for DISU
        elif nxyz is not None:
            self.nxyz = int(nxyz)
            self.grid_shape = (self.nxyz,)

        if self.solutions.ic is None:
            self.solutions.ic = [1]*self.nxyz
        if isinstance(self.solutions.ic, (int, float)):
            self.solutions.ic = np.reshape([self.solutions.ic]*self.nxyz, self.grid_shape)
            print(self.solutions.ic.shape, self.nxyz, self.grid_shape)
        assert (self.solutions.ic.shape == self.grid_shape,
            f'Initial conditions array must be an array of the shape ({self.grid_shape}) not {self.solutions.ic.shape}'
        )
    def set_componenth2o(self, flag):
        '''Set the component H2O to be True or False.
        if False Total H and Total O are transported
        if True H2O, Excess H and Excess O are transported'''
        assert(flag, (bool))
        self.componenth2o = flag
        return self.componenth2o

    def get_componenth2o(self):
        '''Get componenth2o flag'''
        return getattr(self, 'componenth2o')

    def set_fixed_components(self, fixed_components):
        '''Set the fixed components for the MF6RTM model. These are the components that are not transported during the simulation.
        '''
        # FIXME: implemented but commented in main coupling loop
        self.fixed_components = fixed_components

    def set_initial_temp(self, temp):
        assert isinstance(temp, (int, float, list)), 'temp must be an int or float'
        # TODO: for non-homogeneous fields allow 3D and 2D arrays
        self.init_temp = temp

    def set_phases(self, phase):
        '''Sets the phases for the MF6RTM model.
        '''
        # Dynamically get the class of the phase object
        phase_class = phase.__class__

        # Check if the phase object's class is in the dictionary of phase types
        if phase_class not in phase_types.values():
            raise AssertionError(f'{phase_class.__name__} is not a recognized phase type')

        # Proceed with the common logic
        if isinstance(phase.ic, (int, float)):
            phase.ic = np.reshape([phase.ic]*self.nxyz, self.grid_shape)
        phase.data = {i: phase.data[key] for i, key in enumerate(phase.data.keys())}
        assert phase.ic.shape == self.grid_shape, f'Initial conditions array must be an array of the shape ({self.nlay}, {self.nrow}, {self.ncol}) not {phase.ic.shape}'

        # Dynamically set the phase attribute based on the class name
        setattr(self, f"{phase_class.__name__.lower().split('phases')[0]}_phases", phase)

    def set_exchange_phases(self, exchanger):
        '''Sets the exchange phases for the MF6RTM model.
        '''
        assert isinstance(exchanger, ExchangePhases), 'exchanger must be an instance of the Exchange class'
        # exchanger.data = {i: exchanger.data[key] for i, key in enumerate(exchanger.data.keys())}
        if isinstance(exchanger.ic, (int, float)):
            exchanger.ic = np.reshape([exchanger.ic]*self.nxyz, self.grid_shape)
        assert exchanger.ic.shape == self.grid_shape, f'Initial conditions array must be an array of the shape ({self.nlay}, {self.nrow}, {self.ncol}) not {exchanger.ic.shape}'
        self.exchange_phases = exchanger

    def set_equilibrium_phases(self, eq_phases):
        '''Sets the equilibrium phases for the MF6RTM model.
        '''
        assert isinstance(eq_phases, EquilibriumPhases), 'eq_phases must be an instance of the EquilibriumPhases class'
        # change all keys from eq_phases so they start from 0
        eq_phases.data = {i: eq_phases.data[key] for i, key in enumerate(eq_phases.data.keys())}
        self.equilibrium_phases = eq_phases
        if isinstance(self.equilibrium_phases.ic, (int, float)):
            self.equilibrium_phases.ic = np.reshape([self.equilibrium_phases.ic]*self.nxyz, self.grid_shape)
        assert self.equilibrium_phases.ic.shape == self.grid_shape, f'Initial conditions array must be an array of the shape ({self.nlay}, {self.nrow}, {self.ncol}) not {self.equilibrium_phases.ic.shape}'

    def set_charge_offset(self, charge_offset):
        """
        Sets the charge offset for the MF6RTM model to handle negative charge values
        """
        self.charge_offset = charge_offset

    def set_chem_stress(
            self,
            chem_stress: ChemStress,
    ) -> None:
        assert isinstance(chem_stress, ChemStress), 'chem_stress must be an instance of the ChemStress class'
        attribute_name = chem_stress.packnme
        setattr(self, attribute_name, chem_stress)

        self.initialize_chem_stress(attribute_name)


    def set_wd(self, wd):
        """
        Sets the working directory for the MF6RTM model.
        """
        # get absolute path of the working directory
        wd = Path(os.path.abspath(wd))
        # joint current directory with wd, check if exist, create if not
        if not wd.exists():
            wd.mkdir(parents=True, exist_ok=True)
        self.wd = wd

    def set_database(self, database):
        """
        Sets the database for the MF6RTM model.

        Parameters:
        database (str): The path to the database file.

        Returns:
        None
        """
        assert os.path.exists(database), f'{database} not found'
        # get absolute path of the database
        database = os.path.abspath(database)
        self.database = database

    def set_postfix(self, postfix):
        """
        Sets the postfix file for the MF6RTM model.

        Parameters:
        postfix (str): The path to the postfix file.

        Returns:
        None
        """
        assert os.path.exists(postfix), f'{postfix} not found'
        self.postfix = postfix

    def set_reaction_temp(self):
        if isinstance(self.init_temp, (int, float)):
            rx_temp = [self.init_temp]*self.nxyz
            print('Using temperatue of {} for all cells'.format(rx_temp[0]))
        elif isinstance(self.init_temp, (list, np.ndarray)):
            rx_temp = [self.init_temp[0]]*self.nxyz
            print('Using temperatue of {} from SOLUTION 1 for all cells'.format(rx_temp[0]))
        self.reaction_temp = rx_temp
        return rx_temp

    def generate_phreeqc_script(self, add_charge_flag=False):
        """
        Generates the phinp file for the MF6RTM model.
        """

        # where to save the phinp file
        filename = os.path.join(self.wd, 'phinp.dat')
        self.phinp = filename
        # assert that database in self.database exists
        assert os.path.exists(self.database), f'{self.database} not found'

        # Check if all compounds are in the database
        names = utils.get_compound_names(self.database)
        assert all([key in names for key in self.solutions.data.keys() if key not in ["pH", "pe"]]), f'Not all compounds are in the database - check: {", ".join([key for key in self.solutions.data.keys() if key not in names and key not in ["pH", "pe"]])}'

        script = ""

        # Convert single values to lists
        for key, value in self.solutions.data.items():
            if not isinstance(value, list):
                self.solutions.data[key] = [value]
        # replace all values in self.solutinons.data that are 0.0 to a very small number
        for key, value in self.solutions.data.items():
            # self.solutions.data[key] = [1e-30 if val == 0.0 else val for val in value]
            self.solutions.data[key] = [val for val in value]

        # Get the number of solutions
        num_solutions = len(next(iter(self.solutions.data.values())))

        # Initialize the list of previous concentrations and phases

        for i in range(num_solutions):
            # Get the current concentrations and phases
            concentrations = {species: values[i] for species, values in self.solutions.data.items()}
            script += utils.handle_block(concentrations, utils.generate_solution_block, i, temp=self.init_temp, water=1)

        # check if self.equilibrium_phases is not None
        if self.equilibrium_phases is not None:
            for i in self.equilibrium_phases.data.keys():
                # Get the current   phases
                phases = self.equilibrium_phases.data[i]
                # check if all equilibrium phases are in the database
                names = utils.get_compound_names(self.database, 'PHASES')
                assert all([key in names for key in phases.keys()]), 'Following phases are not in database: '+', '.join(f'{key}' for key in phases.keys() if key not in names)

                # Handle the  EQUILIBRIUM_PHASES blocks
                script += utils.handle_block(phases, utils.generate_phases_block, i)

        # check if self.exchange_phases is not None
        if self.exchange_phases is not None:
            # Get the current   phases
            phases = self.exchange_phases.data
            # check if all exchange phases are in the database
            names = utils.get_compound_names(self.database, 'EXCHANGE')
            assert all([key in names for key in phases.keys()]), 'Following are not in database: '+', '.join(f'{key}' for key in phases.keys() if key not in names)

            num_exch = len(next(iter(self.exchange_phases.data.values())))
            for i in range(num_exch):
                # Get the current concentrations and phases
                concentrations = {species: values[i] for species, values in self.exchange_phases.data.items()}
                script += utils.handle_block(concentrations, utils.generate_exchange_block, i, equilibrate_solutions=self.exchange_phases.eq_solutions)

        # check if self.kinetic_phases is not None
        if self.kinetic_phases is not None:
            for i in self.kinetic_phases.data.keys():
                # Get the current   phases
                phases = self.kinetic_phases.data[i]
                # check if all kinetic phases are in the database
                names = []
                for blocknme in ['PHASES', 'SOLUTION_MASTER_SPECIES']:
                    names += utils.get_compound_names(self.database, blocknme)

                assert all([key in names for key in phases.keys()]), 'Following phases are not in database: '+', '.join(f'{key}' for key in phases.keys() if key not in names)

                script += utils.handle_block(phases, utils.generate_kinetics_block, i)

        if self.surfaces_phases is not None:
            for i in self.surfaces_phases.data.keys():
                # Get the current   phases
                phases = self.surfaces_phases.data[i]
                # check if all surfaces are in the database
                names = utils.get_compound_names(self.database, 'SURFACE_MASTER_SPECIES')
                assert all([key in names for key in phases.keys()]), 'Following phases are not in database: '+', '.join(f'{key}' for key in phases.keys() if key not in names)
                script += utils.handle_block(phases, utils.generate_surface_block, i, options=self.surfaces_phases.options)

        # add end of line before postfix
        script += utils.endmainblock

        # Append the postfix file to the script
        if self.postfix is not None and os.path.isfile(self.postfix):
            with open(self.postfix, 'r') as source:  # Open the source file in read mode
                script += '\n'
                script += source.read()

        if add_charge_flag:
            script = utils.add_charge_flag_to_species_in_solution(script)

        with open(filename, 'w') as file:
            file.write(script)
        return script

    def initialize(self, nthreads=1, add_charge_flag=False):
        '''Initialize a PhreeqcRM object to calculate initial concentrations
        from a PHREEQC inputs, adding the following attributes to the Mup3d
        object:

        self.components: list of transportable components
        self.init_conc_array_phreeqc: A 1D array of concentrations (mol/L)
            structured for PhreeqcRM, with each component conc for each grid
            cell ordered by `model.components`
        self.sconc: A dictionary with components as keys and values as an array
            of concentrations (mol/m^3) structured to match the shape of the
            Modflow6 model domain grid

        and others...
        '''
        # get model dis info
        # dis = sim.get_model(sim.model_names[0]).dis

        # create phinp
        # check if phinp.dat is in wd
        phinp = self.generate_phreeqc_script(add_charge_flag=add_charge_flag)

        # initialize phreeqccrm object
        self.phreeqc_rm = phreeqcrm.PhreeqcRM(self.nxyz, nthreads)
        status = self.phreeqc_rm.SetComponentH2O(self.componenth2o)
        self.phreeqc_rm.UseSolutionDensityVolume(False)

        # Open files for phreeqcrm logging
        status = self.phreeqc_rm.SetFilePrefix(os.path.join(self.wd, '_phreeqc'))
        self.phreeqc_rm.OpenFiles()

        # Set concentration units
        status = self.phreeqc_rm.SetUnitsSolution(2)
        # status = self.phreeqc_rm.SetUnitsExchange(1)
        # status = self.phreeqc_rm.SetUnitsSurface(1)
        # status = self.phreeqc_rm.SetUnitsKinetics(1)

        # mf6 handles poro . set to 1
        poro = np.full((self.nxyz), 1.)
        status = self.phreeqc_rm.SetPorosity(poro)

        print_chemistry_mask = np.full((self.nxyz), 1)
        status = self.phreeqc_rm.SetPrintChemistryMask(print_chemistry_mask)
        nchem = self.phreeqc_rm.GetChemistryCellCount()
        self.nchem = nchem

        # Set printing of chemistry file
        status = self.phreeqc_rm.SetPrintChemistryOn(False, True, False)  # workers, initial_phreeqc, utility

        # Load database
        status = self.phreeqc_rm.LoadDatabase(self.database)
        status = self.phreeqc_rm.RunFile(True, True, True, self.phinp)

        # Clear contents of workers and utility
        input = "DELETE; -all"
        status = self.phreeqc_rm.RunString(True, False, True, input)

        # Get component information - these two functions need to be invoked to find comps
        ncomps = self.phreeqc_rm.FindComponents()
        components = list(self.phreeqc_rm.GetComponents())
        self.ncomps = ncomps

        # set components as attribute
        self.components = components

        # Initial equilibration of cells
        time = 0.0
        time_step = 0.0
        status = self.phreeqc_rm.SetTime(time)
        status = self.phreeqc_rm.SetTimeStep(time_step)

        ic1 = np.ones((self.nxyz, 7), dtype=int)*-1

        # this gets a column slice
        ic1[:, 0] = np.reshape(self.solutions.ic, self.nxyz)

        if isinstance(self.equilibrium_phases, EquilibriumPhases):
            ic1[:, 1] = np.reshape(self.equilibrium_phases.ic, self.nxyz)
        if isinstance(self.exchange_phases, ExchangePhases):
            ic1[:, 2] = np.reshape(self.exchange_phases.ic, self.nxyz)  # Exchange
        if isinstance(self.surfaces_phases, Surfaces):
            ic1[:, 3] = np.reshape(self.surfaces_phases.ic, self.nxyz)  # Surface
        ic1[:, 4] = -1  # Gas phase
        ic1[:, 5] = -1  # Solid solutions
        if isinstance(self.kinetic_phases, KineticPhases):
            ic1[:, 6] = np.reshape(self.kinetic_phases.ic, self.nxyz)  # Kinetics

        ic1_flatten = ic1.flatten('F')

        # set initial conditions as attribute but in a new sub class
        self.ic1 = ic1
        self.ic1_flatten = ic1_flatten

        # initialize ic1 phreeqc to module with phrreeqcrm
        status = self.phreeqc_rm.InitialPhreeqc2Module(ic1_flatten)

        # get initial concentrations from running phreeqc
        status = self.phreeqc_rm.RunCells()
        c_dbl_vect = self.phreeqc_rm.GetConcentrations()
        self.init_conc_array_phreeqc = c_dbl_vect

        conc = [c_dbl_vect[i:i + self.nxyz] for i in range(0, len(c_dbl_vect), self.nxyz)]

        self.sconc = {}

        for i, c in enumerate(components):
            # where thelement is a component name (c)
            get_conc = np.reshape(conc[i], self.grid_shape)
            get_conc = utils.concentration_l_to_m3(get_conc)
            if c.lower() == 'charge':
                get_conc += self.charge_offset
            self.sconc[c] = get_conc

        self.set_reaction_temp()
        self.write_simulation()
        print('Phreeqc initialized')
        return

    def set_config(self, **kwargs) -> MF6RTMConfig:
        """Create and store a config object."""
        self.config = MF6RTMConfig(**kwargs)
        return self.config

    def get_config(self):
        """Retrieve config object"""
        return self.config.to_dict()

    def save_config(self):
        """Save config toml file"""
        assert self.wd is not None, "Model directory not specified"
        config_path = self.wd / "mf6rtm.toml"
        self.config.save_to_file(filepath=config_path)
        return config_path

    def write_simulation(self):
        """write phreqcrm simulation and configuration files"""
        self._write_phreeqc_init_file()
        self.save_config()
        print(f"Simulation saved in {self.wd}")
        return

    def initialize_chem_stress(
        self,
        attr: str,
        nthreads: int = 1,
    ) -> dict:
        """Initialize a PhreeqcRM object with boundary condition chemical
        concentrations for the specified Modflow Stress Period and Package.

        Parameters
        ----------
        attr : str
            The Modflow 6 Package name.
        nthreads : int, optional
            Number of threads to use for PhreeqcRM (default is 1).

        Returns
        -------
        dict
            Dictionary with component names as keys and concentration arrays in moles/m3 as values.

        Notes
        -----
        This function initializes a PhreeqcRM object, loads a database, runs a Phreeqc input file,
        and transfers solutions and reactants to the reaction-module workers. It then equilibrates
        the cells, gets the concentrations, and converts them to moles/m3.

        See Also
        --------
        phreeqcrm.PhreeqcRM : PhreeqcRM class documentation.
        """
        print('Initializing ChemStress')
        # check if self has a an attribute that is a class ChemStress but without knowing the attribute name
        chem_stress = [attr for attr in dir(self) if isinstance(getattr(self, attr), ChemStress)]

        assert len(chem_stress) > 0, 'No ChemStress attribute found in self'

        # Get total number of grid cells affected by the stress period
        nxyz_spd = len(getattr(self, attr).sol_spd)

        phreeqc_rm = phreeqcrm.PhreeqcRM(nxyz_spd, nthreads)
        status = phreeqc_rm.SetComponentH2O(self.componenth2o)
        phreeqc_rm.UseSolutionDensityVolume(False)

        # Set concentration units
        status = phreeqc_rm.SetUnitsSolution(2)

        poro = np.full((nxyz_spd), 1.)
        status = phreeqc_rm.SetPorosity(poro)
        print_chemistry_mask = np.full((nxyz_spd), 1)
        status = phreeqc_rm.SetPrintChemistryMask(print_chemistry_mask)
        nchem = phreeqc_rm.GetChemistryCellCount()

        # Set printing of chemistry file
        status = phreeqc_rm.SetPrintChemistryOn(False, True, False)  # workers, initial_phreeqc, utility

        # Load database
        status = phreeqc_rm.LoadDatabase(self.database)
        status = phreeqc_rm.RunFile(True, True, True, self.phinp)

        # Clear contents of workers and utility
        input = "DELETE; -all"
        status = phreeqc_rm.RunString(True, False, True, input)

        # Get component information - these two functions need to be invoked to find comps
        ncomps = phreeqc_rm.FindComponents()
        components = list(phreeqc_rm.GetComponents())

        # Transfer solutions and reactants from the InitialPhreeqc instance to
        # the reaction-module workers. See https://usgs-coupled.github.io/phreeqcrm/namespacephreeqcrm.html#ac3d7e7db76abda97a3d11b3ff1903322
        ic1 = [-1] * nxyz_spd * 7
        for e, i in enumerate(getattr(self, attr).sol_spd):
            # TODO: modify to conform to the index, element convention
            #       (i and e are reversed in line above)
            ic1[e] = i  # Solution 1
            # TODO: implment other ic1 blocks
            # ic1[nxyz_spd + i]     = -1  # Equilibrium phases none
            # ic1[2 * nxyz_spd + i] =  -1  # Exchange 1
            # ic1[3 * nxyz_spd + i] = -1  # Surface none
            # ic1[4 * nxyz_spd + i] = -1  # Gas phase none
            # ic1[5 * nxyz_spd + i] = -1  # Solid solutions none
            # ic1[6 * nxyz_spd + i] = -1  # Kinetics none
        status = phreeqc_rm.InitialPhreeqc2Module(ic1)

        # Initial equilibration of cells
        time = 0.0
        time_step = 0.0
        status = phreeqc_rm.SetTime(time)
        status = phreeqc_rm.SetTimeStep(time_step)

        # status = phreeqc_rm.RunCells()
        c_dbl_vect = phreeqc_rm.GetConcentrations()
        c_dbl_vect = utils.concentration_l_to_m3(c_dbl_vect)

        c_dbl_vect = [c_dbl_vect[i:i + nxyz_spd] for i in range(0, len(c_dbl_vect), nxyz_spd)]

        # find charge in c_dbl_vect and add charge_offset
        for i, c in enumerate(components):
            if c.lower() == 'charge':
                c_dbl_vect[i] += self.charge_offset

        sconc = {}
        for i in range(nxyz_spd):
            sconc[i] = [array[i] for array in c_dbl_vect]

        status = phreeqc_rm.CloseFiles()
        status = phreeqc_rm.MpiWorkerBreak()

        # set as attribute
        setattr(getattr(self, attr), 'data', sconc)
        setattr(getattr(self, attr), 'auxiliary', components)
        print(f'ChemStress {attr} initialized')
        return sconc

    def _initialize_phreeqc_from_file(self, yamlfile):
        '''Initialize phreeqc from a yaml file'''
        yamlfile = self.phreeqcyaml_file
        phreeqcrm_from_yaml = phreeqcrm.InitializeYAML(yamlfile)
        if self.phreeqc_rm is None:
            self.phreeqc_rm = phreeqcrm_from_yaml
        return

    def _write_phreeqc_init_file(self, filename='mf6rtm.yaml'):
        '''Write the phreeqc init yaml file'''
        fdir = os.path.join(self.wd, filename)
        phreeqcrm_yaml = yamlphreeqcrm.YAMLPhreeqcRM()
        phreeqcrm_yaml.YAMLSetGridCellCount(self.nxyz)
        phreeqcrm_yaml.YAMLThreadCount(1)
        status = phreeqcrm_yaml.YAMLSetComponentH2O(self.componenth2o)
        status = phreeqcrm_yaml.YAMLUseSolutionDensityVolume(False)

        # Open files for phreeqcrm logging
        status = phreeqcrm_yaml.YAMLSetFilePrefix(os.path.join(self.wd, '_phreeqc'))
        status = phreeqcrm_yaml.YAMLOpenFiles()

        # set some properties
        phreeqcrm_yaml.YAMLSetErrorHandlerMode(1)
        phreeqcrm_yaml.YAMLSetRebalanceFraction(0.5) # Needed for multithreading
        phreeqcrm_yaml.YAMLSetRebalanceByCell(True) # Needed for multithreading
        phreeqcrm_yaml.YAMLSetPartitionUZSolids(False) # TODO: implement when UZF is turned on

        # Set concentration units
        phreeqcrm_yaml.YAMLSetUnitsSolution(2)       # 1, mg/L; 2, mol/L; 3, kg/kgs
        phreeqcrm_yaml.YAMLSetUnitsPPassemblage(1)   # 0, mol/L cell; 1, mol/L water; 2 mol/L rock
        phreeqcrm_yaml.YAMLSetUnitsExchange(1)       # 0, mol/L cell; 1, mol/L water; 2 mol/L rock
        phreeqcrm_yaml.YAMLSetUnitsSurface(1)        # 0, mol/L cell; 1, mol/L water; 2 mol/L rock
        phreeqcrm_yaml.YAMLSetUnitsGasPhase(1)       # 0, mol/L cell; 1, mol/L water; 2 mol/L rock
        phreeqcrm_yaml.YAMLSetUnitsSSassemblage(1)   # 0, mol/L cell; 1, mol/L water; 2 mol/L rock
        phreeqcrm_yaml.YAMLSetUnitsKinetics(1)       # 0, mol/L cell; 1, mol/L water; 2 mol/L rock

        # mf6 handles poro . set to 1
        poro = [1.0]*self.nxyz
        status = phreeqcrm_yaml.YAMLSetPorosity(list(poro))

        print_chemistry_mask = [1]*self.nxyz
        assert all(isinstance(i, int) for i in print_chemistry_mask), 'print_chemistry_mask length must be equal to the number of grid cells'
        status = phreeqcrm_yaml.YAMLSetPrintChemistryMask(print_chemistry_mask)
        status = phreeqcrm_yaml.YAMLSetPrintChemistryOn(False, True, False)  # workers, initial_phreeqc, utility

        rv = [1] * self.nxyz
        phreeqcrm_yaml.YAMLSetRepresentativeVolume(rv)

        # Load database
        status = phreeqcrm_yaml.YAMLLoadDatabase(self.database)
        status = phreeqcrm_yaml.YAMLRunFile(True, True, True, self.phinp)

        # Clear contents of workers and utility
        input = "DELETE; -all"
        status = phreeqcrm_yaml.YAMLRunString(True, False, True, input)
        phreeqcrm_yaml.YAMLAddOutputVars("AddOutputVars", "true")

        status = phreeqcrm_yaml.YAMLFindComponents()
        # convert ic1 to a list
        ic1_flatten = self.ic1_flatten

        status = phreeqcrm_yaml.YAMLInitialPhreeqc2Module(ic1_flatten)
        status = phreeqcrm_yaml.YAMLRunCells()
        # Initial equilibration of cells
        time = 0.0
        status = phreeqcrm_yaml.YAMLSetTime(time)
        # status = phreeqcrm_yaml.YAMLSetTimeStep(time_step)
        status = phreeqcrm_yaml.WriteYAMLDoc(fdir)

        # create new attribute for phreeqc yaml file
        self.phreeqcyaml_file = fdir
        self.phreeqcrm_yaml = phreeqcrm_yaml
        return

    def run(self, reactive = None, nthread=1):
        '''Wrapper function to run the MF6RTM model'''
        return solve(self.wd, reactive=reactive, nthread=nthread)
