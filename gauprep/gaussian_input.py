import configparser
from decimal import Decimal
from pathlib import Path
from typing import Optional, Union, Tuple, List

from gauprep.gbs_parser import GaussianBasisData
from config import EXTERNAL_BASIS_DIR, DEFAULT_ROUTE_KEYWORDS, D3ZERO_PARAM_FILE, D3BJ_PARAM_FILE, ATOM_LIST


def get_gbs_path(name: str) -> Optional[Path]:
    external_basis_dir = Path(__file__).absolute().parent.parent / EXTERNAL_BASIS_DIR
    # For case-insensitive matching, do reverse brute force search.
    for gbs_file in external_basis_dir.glob('*.gbs'):
        if gbs_file.stem.lower() == name.lower():
            return gbs_file.absolute()
    return None


def get_gen_basis_string(atoms: List[str], basis_name: str) -> str:
    basis_string = ' '.join(atoms) + ' 0\n'
    basis_string += basis_name + '\n'
    basis_string += '****\n'
    return basis_string


def get_gen_ecp_string(atoms: List[str], ecp_name: str) -> str:
    ecp_string = ' '.join(atoms) + ' 0\n'
    ecp_string += ecp_name + '\n'
    return ecp_string


def get_atom_list(structure_data: List[str], n_h: int) -> Tuple[List[str], List[str]]:
    """
    Return light atom list and heavy atom list from Gaussian's structure data
    n_h: atoms of atomic number of n_h or larger are classified as heavy atom.
    :return: List[str], List[str] light atoms and heavy atoms
    """

    atoms_check = [False] * 130  # index=0 = bq, check flag if the atomic number of index is used
    l_atom = []
    h_atom = []

    for line in structure_data:
        terms = line.strip().split()  # terms[0] should be atomic symbol
        for (atom_number, atom) in enumerate(ATOM_LIST):
            if terms[0].upper() == atom.upper():
                atoms_check[atom_number] = True

    atoms_check[0] = False  # ignore ghost atom

    for (atom_number, atom) in enumerate(ATOM_LIST):
        if atoms_check[atom_number]:
            if atom_number < n_h:
                l_atom.append(atom)
            else:
                h_atom.append(atom)

    return l_atom, h_atom


def join_terms(terms: List[str], limit: int = 80):
    result = ''
    current_length = 0

    for term in terms:
        if current_length + len(term) <= limit:
            result += term + ' '
            current_length += len(term) + 1
        else:
            result = result.rstrip()
            result += '\n'
            result += term + ' '
            current_length = len(term) + 1

    return result.rstrip() + '\n'


def generate_dispersion_iop_terms(dispersion_method: str, functional: str) -> str:

    d3zero_names = ['GD3', 'GD3ZERO', 'D3', 'D3ZERO']
    d3bj_names = ['GD3BJ', 'D3BJ']
    d2_names = ['GD2', 'D2']

    if dispersion_method.upper() in d3zero_names:
        param_file = D3ZERO_PARAM_FILE
    elif dispersion_method.upper() in d3bj_names:
        param_file = D3BJ_PARAM_FILE
    elif dispersion_method.upper() in d2_names:
        raise RuntimeError('GD2 dispersion with an external parameter file is not implemented.')
    else:
        raise ValueError('DFT-D version name is not valid.')

    params = configparser.ConfigParser()
    params.read(param_file)

    # section name = functional name
    if not params.has_section(functional.upper()):
        raise ValueError('Valid DFT-D3 parameters for this functional is not found.')

    iop_terms = []

    def _format_value(value):
        v = '{:f}'.format(Decimal(value) * 1000000).split('.')[0]
        return '{:0>7}'.format(v)

    # IOp(3/174)
    # S6 scale factor in Grimme’s D2/D3/D3BJ dispersion.
    # NNNNNNNN	A value of NNNNNNNN/1000000.
    if dispersion_method.upper() in d3zero_names + d3bj_names:
        s6 = params.get(functional.upper(), 's6')
        iop_terms.append('3/174=' + _format_value(s6))

    # IOp(3/175)
    # S8 scale factor in Grimme’s D2/D3/D3BJ dispersion.
    # NNNNNNNN	A value of NNNNNNNN/1000000.
    if dispersion_method.upper() in d3zero_names + d3bj_names:
        s8 = params.get(functional.upper(), 's8')
        iop_terms.append('3/175=' + _format_value(s8))

    # IOp(3/176)
    # SR6 scale factor in Grimme’s D2/D3/D3BJ dispersion. D3BJ -> default
    # 0	Default (see subroutine R6DSR6).
    # -1	Set SR6 to 0.
    # NNNNNNNN	A value of NNNNNNNN/1000000.
    # for D3zero
    if dispersion_method.upper() in d3zero_names:
        sr6 = params.get(functional.upper(), 'sr6')
        iop_terms.append('3/176=' + _format_value(sr6))
    # default for D3BJ
    if dispersion_method.upper() in d3bj_names:
        iop_terms.append('3/176=0')

    # IOp(3/177)
    # A1 parameter in Becke-Johnson damping for D3BJ and XDM.
    # 0	Default (see subroutine R6DABJ/XDMABJ).
    # -1	Set A1 to 0.
    # NNNNNNNN	A value of NNNNNN/1000000.
    if dispersion_method.upper() in d3bj_names:
        a1 = params.get(functional.upper(), 'a1')
        iop_terms.append('3/177=' + _format_value(a1))

    # IOp(3/178)
    # A2 parameter in Becke-Johnson damping for D3BJ and XDM.
    # 0	Default (see subroutine R6DABJ/XDMABJ).
    # -1	Set A2 to 0.
    # NNNNNNNN	A value of NNNNNN/1000000 Ang.
    if dispersion_method.upper() in d3bj_names:
        a2 = params.get(functional.upper(), 'a2')
        iop_terms.append('3/178=' + _format_value(a2))

    return 'iOp({:})'.format(','.join(iop_terms))


class GaussianInputData:

    def __init__(self, charge: int, multiplicity: int, structure: List[str]):

        self.file_stem = ''
        self.charge: int = charge
        self.multiplicity: int = multiplicity
        self.structure: List[str] = structure
        # sanitize the structure
        structure[-1] = structure[-1].rstrip() + '\n'

        self.n_proc = ''  # '', int >= 1
        self.memory = ''  # ''

        self.title = ''

        self.job_type = 'Opt+Freq'  # SP, Freq, Opt, Opt+Freq, TS, IRC, WFX, NBO, ANY
        self.method = 'B3LYP'  # functional name or HF, MP2
        self.basis = 'def2SVP'  # basis name
        self.basis_h_ecp = 'def2SVP'  # basis name
        self.ecp_for_3d = False  # True for apply ECP basis set to 3d metal row atoms

        self.solvation = 'none'  # none, PCM, CPCM, SMD
        self.solvent = 'Chloroform'  # solvent name

        self.dispersion = 'none'  # none, GD3, GD3BJ, D2
        self.dispersion_external_param = False  # True > read DFT-D parameters from seting file and put iop.

        self.nosymm = False  # True for add nosymm to inhibit orientation change

        self.opt_convergence = 'default'  # loose, default, tight, verytight
        self.opt_maxcycle = ''  # '',  int > 0
        self.opt_maxstep = ''  # '', int > 0
        self.opt_calcfc = ''  # '', 0 for calcfc, 1 for calcall, int > 1 for recalcfc
        self.opt_algorithm = 'default'  # default, GDIIS, Newton
        self.opt_modredundant = ''

        self.irc_direction = 'both'  # both, forward, reverse
        self.irc_algorithm = 'lqa'  # hpc, eulerpc, lqa
        self.irc_maxpoints = ''  # '', int > 0
        self.irc_stepsize = ''  # '', int > 0
        self.irc_maxcyc = ''  # '', int > 0
        self.irc_calcfc_predictor = ''  # '', int > 0
        self.irc_calcfc_corrector = ''  # '', int > 0

        self.nbo_version = 'Gaussian'  # Gaussian, 6, 7.  call nbo, nbo6, nbo7
        self.nbo_keywords = []  # keyword list for nboread sections
        self.nbo_save = False  # True for add savenbos to save NBO in chk file

        self.any_job_input = ''

        self.first_stable_check = False
        self.guess_mix = False

    @property
    def charge(self):
        return self._charge

    @charge.setter
    def charge(self, value):
        value = str(value).strip()
        try:
            value = int(value)
        except:
            raise ValueError('Charge should be integer.')
        else:
            self._charge = value

    @property
    def multiplicity(self):
        return self._multiplicity

    @multiplicity.setter
    def multiplicity(self, value):
        value = str(value).strip()
        try:
            value = int(value)
            assert value >= 1
        except:
            raise ValueError('Multiplicity should be positive integer.')
        else:
            self._multiplicity = value

    @property
    def n_proc(self):
        return self._n_proc

    @n_proc.setter
    def n_proc(self, value):
        value = value.strip()
        if value == '':
            self._n_proc = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('The number of CPUs (n_proc) should be positive integer.')
            else:
                self._n_proc = value

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, value):
        self._memory = value.strip()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value.strip()

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, value):
        self._method = value.strip()

    @property
    def basis(self):
        return self._basis

    @basis.setter
    def basis(self, value):
        self._basis = value.strip()

    @property
    def basis_h_ecp(self):
        return self._basis_h_ecp

    @basis_h_ecp.setter
    def basis_h_ecp(self, value):
        self._basis_h_ecp = value.strip()

    @property
    def solvent(self):
        return self._solvent

    @solvent.setter
    def solvent(self, value):
        self._solvent = value.strip()

    @property
    def nosymm(self):
        return self._nosymm

    @nosymm.setter
    def nosymm(self, value):
        self._nosymm = bool(value)

    @property
    def opt_maxcycle(self):
        return self._opt_maxcycle

    @opt_maxcycle.setter
    def opt_maxcycle(self, value):
        value = value.strip()
        if value == '':
            self._opt_maxcycle = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Maxcycle for Opt (opt_maxcycle) should be positive integer.')
            else:
                self._opt_maxcycle = value

    @property
    def opt_maxstep(self):
        return self._opt_maxstep

    @property
    def opt_modredundant(self):
        return self._opt_modredundant

    @opt_modredundant.setter
    def opt_modredundant(self, value):
        lines = []
        for line in value.splitlines():
            line = line.strip()
            if line != '':
                lines.append(line)
        if len(lines) == 0:
            self._opt_modredundant = ''
        else:
            self._opt_modredundant = '\n'.join(lines) + '\n'

    def is_modredundant_valid(self):
        return not self.opt_modredundant == ''

    @opt_maxstep.setter
    def opt_maxstep(self, value):
        value = value.strip()
        if value == '':
            self._opt_maxstep = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Maxstep for Opt (opt_maxstep) should be positive integer.')
            else:
                self._opt_maxstep = value

    @property
    def opt_calcfc(self):
        return self._opt_calcfc

    @opt_calcfc.setter
    def opt_calcfc(self, value):
        value = value.strip()
        if value == '':
            self._opt_calcfc = value
        else:
            try:
                v = int(value)
                assert v >= 0
            except:
                raise ValueError('Calcfc for Opt (opt_calcfc) should be 0 (calcfc)'
                                 ' or 1 (calcall) or positive integer (recalcfc).')
            else:
                self._opt_calcfc = value

    @property
    def irc_maxpoints(self):
        return self._irc_maxpoints

    @irc_maxpoints.setter
    def irc_maxpoints(self, value):
        value = value.strip()
        if value == '':
            self._irc_maxpoints = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Maxpoints for IRC (irc_maxpoints) should be positive integer.')
            else:
                self._irc_maxpoints = value

    @property
    def irc_stepsize(self):
        return self._irc_stepsize

    @irc_stepsize.setter
    def irc_stepsize(self, value):
        value = value.strip()
        if value == '':
            self._irc_stepsize = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Stepsize for IRC (irc_stepsize) should be positive integer.')
            else:
                self._irc_stepsize = value

    @property
    def irc_maxcyc(self):
        return self._irc_maxcyc

    @irc_maxcyc.setter
    def irc_maxcyc(self, value):
        value = value.strip()
        if value == '':
            self._irc_maxcyc = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Maxcycles in each optimization for IRC (irc_maxcyc) should be positive integer.')
            else:
                self._irc_maxcyc = value

    @property
    def irc_calcfc_predictor(self):
        return self._irc_calcfc_predictor

    @irc_calcfc_predictor.setter
    def irc_calcfc_predictor(self, value):
        value = value.strip()
        if value == '':
            self._irc_calcfc_predictor = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Recalcfc for predictor step in IRC (irc_calcfc_predictor)'
                                 ' should be positive integer.')
            else:
                self._irc_calcfc_predictor = value

    @property
    def irc_calcfc_corrector(self):
        return self._irc_calcfc_corrector

    @irc_calcfc_corrector.setter
    def irc_calcfc_corrector(self, value):
        value = value.strip()
        if value == '':
            self._irc_calcfc_corrector = value
        else:
            try:
                v = int(value)
                assert v > 0
            except:
                raise ValueError('Recalcfc for corrector step in IRC (irc_calcfc_corrector)'
                                 ' should be positive integer.')
            else:
                self._irc_calcfc_corrector = value

    def output_file(self, file: Union[Path, str]):
        file = Path(file)
        self.file_stem = file.stem

        output_data = []
        read_prev = False  # change True when one calculation block is set (for sequential job)

        # SP type job is always a single job.
        if self.job_type.upper() in ['SP', 'NBO', 'WFX', 'ANY']:
            output_data.extend(self._get_output_block(job_type=self.job_type.upper(),
                                                      read_prev=read_prev,
                                                      stableopt=self.first_stable_check))

        # For other jobs
        else:
            # in case stable=opt job
            if self.first_stable_check:
                output_data.extend(self._get_output_block(job_type='SP', read_prev=read_prev, stableopt=True))
                read_prev = True

            # in case OPT+FREQ job with iop D3 parameter settings >> OPT Link1 FREQ 2 step job.
            if self.job_type.upper() in ['OPT+FREQ', 'TS'] and \
                    self.dispersion.lower() != 'none' and \
                    self.dispersion_external_param:
                output_data.extend(self._get_output_block(job_type='OPT', read_prev=read_prev, stableopt=False))
                read_prev = True
                output_data.extend(self._get_output_block(job_type='FREQ', read_prev=read_prev, stableopt=False))

            # for other cases
            else:
                output_data.extend(self._get_output_block(job_type=self.job_type.upper(),
                                                          read_prev=read_prev, stableopt=False))

        with file.open(mode='w', encoding='utf-8', newline='\n') as f:
            f.writelines(output_data)

    def _get_output_block(self, job_type: str, read_prev: bool, stableopt: bool) -> List[str]:
        gen_basis_ecp_string = self._get_gen_ecp_string()  # This should be run to check gen pseudo=read

        output_block = []
        if read_prev:
            output_block.append('--Link1--\n')
        output_block.append(self._get_link0_string())
        output_block.append('%chk=' + self.file_stem + '.chk\n')
        output_block.append(self._get_route_string(job_type=job_type, read_prev=read_prev, stableopt=stableopt))
        output_block.append('\n')
        if not read_prev:
            output_block.append(self._get_title_string())
            output_block.append('\n')
            output_block.append('{:} {:}\n'.format(self.charge, self.multiplicity))
            output_block.extend(self.structure)
            output_block.append('\n')
        # modredundant
        if job_type.upper() in ['OPT', 'OPT+FREQ'] and self.is_modredundant_valid():
            output_block.append(self.opt_modredundant)
            output_block.append('\n')
        # additional sections
        # Gen/ECP
        if gen_basis_ecp_string is not None:
            output_block.append(gen_basis_ecp_string)
            output_block.append('\n')
        # NBO input
        if self.job_type.upper() == 'NBO':
            output_block.append(' '.join(['$NBO'] + self.nbo_keywords + ['$END']) + '\n')
            output_block.append('\n')
        # output wfx file
        if self.job_type.upper() == 'WFX':
            output_block.append(self.file_stem + '.wfx\n')
            output_block.append('\n')

        # ensure that just one blank line exist at the block end
        if output_block[-1] != '\n':
            output_block.append('\n')
        if output_block[-2] == '\n':
            output_block = output_block[:-1]

        return output_block

    def _get_link0_string(self) -> str:
        link0 = []
        self.n_proc = self.n_proc.strip()
        if self.n_proc:
            link0.append('%nprocshared=' + self.n_proc)
        self.memory = self.memory.strip()
        if self.memory:
            link0.append('%mem=' + self.memory)
        link0_string = '\n'.join(link0) + '\n'
        if link0_string.strip() == '':
            return ''
        else:
            return link0_string

    def _get_title_string(self) -> str:
        if self.title.strip() == '':
            return 'NO TITLE\n'
        else:
            title_string = self.title.strip().replace('\n', ' ')

            # replace ${GEN} field
            if '${GEN}' in title_string:
                gen_details_string = ''
                if self.gen_basis:
                    if len(self.atoms_l) > 0:
                        gen_details_string += self.basis + ' for ' + ','.join(self.atoms_l)
                    if len(self.atoms_h) > 0:
                        if gen_details_string != '':
                            gen_details_string += ' and '
                        gen_details_string += self.basis_h_ecp + ' for ' + ','.join(self.atoms_h)
                title_string = title_string.replace('${GEN}', gen_details_string)

            # replace ${FILENAME} field
            if '${FILENAME}' in title_string:
                title_string = title_string.replace('${FILENAME}', self.file_stem)

            return title_string.rstrip() + '\n'

    def _get_route_string(self, job_type: str, read_prev: bool, stableopt: bool) -> str:
        route_terms = ['#P']

        # Job terms
        # job type that can be combined with stable=opt (single point jobs)
        if job_type.upper() in ['SP', 'WFX', 'NBO', 'ANY']:
            if stableopt:
                route_terms.append('stable=opt')
            else:
                route_terms.append('SP')
            # add additional terms
            if job_type.upper() == 'WFX':
                route_terms.append(self._get_wfx_term())
            elif job_type.upper() == 'NBO':
                route_terms.append(self._get_nbo_term())
            elif job_type.upper() == 'ANY':
                route_terms.append(self.any_job_input.strip())
        else:
            if stableopt:
                raise RuntimeError('Stable=opt and ' + job_type + 'are not compatible.')

        if job_type.upper() == "FREQ":
            route_terms.append('FREQ=noraman')
        elif job_type.upper() == "OPT":
            route_terms.append(self._get_opt_term())
        elif job_type.upper() == 'OPT+FREQ':
            route_terms.append(self._get_opt_term())
            if self.opt_calcfc != '1':
                route_terms.append('FREQ=noraman')
        elif job_type.upper() == 'TS':
            route_terms.append(self._get_optts_term())
            if self.opt_calcfc != '1':
                route_terms.append('FREQ=noraman')
        elif job_type.upper() == 'IRC':
            route_terms.append(self._get_irc_term())

        if self.multiplicity != 1:
            prefix = 'U'
        elif stableopt:
            prefix = 'U'
        elif read_prev and self.first_stable_check:
            prefix = 'U'
        else:
            prefix = ''

        # Method and solvation terms
        route_terms.append(self._get_method_term(prefix))
        route_terms.append(self._get_solvation_term())

        # dispersion
        if self.dispersion.lower() != 'none':
            route_terms.append('empiricaldispersion={:}'.format(self.dispersion))

        # nosymm
        if self.nosymm:
            route_terms.append('nosymm')

        # read checkpoint for read prev
        if read_prev:
            route_terms.extend(['guess=read', 'geom=allcheck'])
        # guess=mix
        elif self.guess_mix:
            route_terms.append('guess=mix')

        # Other terms
        route_terms.append(self._get_other_setting_term())

        # iop for dispersion
        if self.dispersion.lower() != 'none' and self.dispersion_external_param:
            route_terms.append(generate_dispersion_iop_terms(dispersion_method=self.dispersion, functional=self.method))

        route_terms = [t for t in route_terms if t is not None]  # exclude None
        route_terms = [t for t in route_terms if t.strip() != '']  # exclude blank string

        return join_terms(route_terms)

    def _get_method_term(self, prefix='') -> str:
        method_terms = [prefix + self.method]
        if self.gen_basis:
            method_terms.append('Gen')
            if self.pseudo_read:
                method_terms.append('Pseudo=read')
        elif len(self.atoms_l) == 0:
            method_terms.append(self.basis_h_ecp)
        else:
            method_terms.append(self.basis)
        return ' '.join(method_terms)

    def _get_solvation_term(self):
        if self.solvation.lower() == 'none':
            return None
        else:
            return 'SCRF=({:},solvent={:})'.format(self.solvation, self.solvent)

    def _get_opt_term(self) -> str:

        opt_options = []
        if self.opt_convergence.lower() != 'default':
            opt_options.append(self.opt_convergence)
        if self.opt_maxcycle != '':
            opt_options.append('maxcycle=' + self.opt_maxcycle)
        if self.opt_maxstep != '':
            opt_options.append('maxstep=' + self.opt_maxstep)
        if self.opt_calcfc == '0':
            opt_options.append('calcfc')
        elif self.opt_calcfc == '1':
            opt_options.append('calcall')
        elif self.opt_calcfc != '':
            opt_options.append('calcfc')
            opt_options.append('recalcfc=' + self.opt_calcfc)
        if self.opt_algorithm.lower() != 'default':
            opt_options.append(self.opt_algorithm)
        if self.is_modredundant_valid():
            opt_options.append('modredundant')

        option_string = ','.join(opt_options)
        option_string = option_string.strip().rstrip(',')

        if option_string == '':
            return 'Opt'
        elif '=' in option_string or ',' in option_string:
            return 'Opt=({:})'.format(option_string)
        else:
            return 'Opt=' + option_string

    def _get_optts_term(self) -> str:

        opt_options = ['TS', 'noeigentest']
        if self.opt_convergence.lower() != 'default':
            opt_options.append(self.opt_convergence)
        if self.opt_maxcycle != '':
            opt_options.append('maxcycle=' + self.opt_maxcycle)
        if self.opt_maxstep != '':
            opt_options.append('maxstep=' + self.opt_maxstep)
        if self.opt_calcfc == '1':
            opt_options.append('calcall')
        elif self.opt_calcfc != '':
            opt_options.append('calcfc')
            opt_options.append('recalcfc=' + self.opt_calcfc)
        else:
            opt_options.append('calcfc')
        if self.opt_algorithm.lower() != 'default':
            opt_options.append(self.opt_algorithm)

        option_string = ','.join(opt_options)
        return 'Opt=({:})'.format(option_string)

    def _get_irc_term(self) -> str:

        irc_options = [self.irc_algorithm]

        if self.irc_algorithm.lower() in ['lqa']:
            irc_options.append('recorrect=never')
        if self.irc_direction.lower() != 'both':
            irc_options.append(self.irc_direction)
        if self.irc_maxpoints != '':
            irc_options.append('maxpoints=' + self.irc_maxpoints)
        if self.irc_stepsize != '':
            irc_options.append('stepsize=' + self.irc_stepsize)
        if self.irc_maxcyc != '' and self.irc_algorithm.lower() not in ['lqa']:
            irc_options.append('maxcyc=' + self.irc_maxcyc)

        irc_options.append('calcfc')

        # case LQA (calcfc only for predictor)
        if self.irc_algorithm.lower() in ['lqa']:
            if self.irc_calcfc_predictor != '':
                irc_options.append('recalc={:}'.format(self.irc_calcfc_predictor))

        # case HPC or EulerPC
        else:
            if self.irc_calcfc_predictor != '' and self.irc_calcfc_corrector == '':
                irc_options.append('recalc={:}'.format(self.irc_calcfc_predictor))
            elif self.irc_calcfc_predictor == '' and self.irc_calcfc_corrector != '':
                irc_options.append('recalc=-{:}'.format(self.irc_calcfc_corrector))
            elif self.irc_calcfc_predictor != '' and self.irc_calcfc_corrector != '':
                irc_options.append('recalcfc=(predictor={:}, corrector={:})'.format(self.irc_calcfc_predictor,
                                                                                    self.irc_calcfc_corrector))

        irc_option_string = ','.join(irc_options)
        if '=' in irc_option_string or ',' in irc_option_string:
            return 'IRC=({:})'.format(irc_option_string)
        else:
            return 'IRC=' + irc_option_string

    def _get_wfx_term(self) -> str:
        if self.multiplicity == 1:
            return 'output=wfx'
        else:
            return 'output=wfx'

    def _get_nbo_term(self) -> str:
        if self.nbo_version.lower() == 'gaussian':
            nbo_name = 'nbo'
        else:
            nbo_name = 'nbo' + str(self.nbo_version).strip()
        if self.nbo_save:
            return 'pop=({:}read,savenbos)'.format(nbo_name)
        else:
            return 'pop={:}read'.format(nbo_name)

    def _get_other_setting_term(self) -> str:
        return DEFAULT_ROUTE_KEYWORDS

    def _get_gen_ecp_string(self) -> Optional[str]:
        atom_num_ecp = 19 if self.ecp_for_3d else 37
        self.atoms_l, self.atoms_h = get_atom_list(self.structure, atom_num_ecp)

        # Check external basis set file. None if not found.
        ext_basis_file = get_gbs_path(self.basis)
        ext_basis_h_file = get_gbs_path(self.basis_h_ecp)

        # Following 3 cases: not necessary to use gen
        # 1. only light atoms, no external file
        # 2. only heavy atoms, no external file
        # 3. light atoms and heavy atoms with the same basis set, no external file
        if (len(self.atoms_h) == 0 and ext_basis_file is None) \
                or (len(self.atoms_l) == 0 and ext_basis_h_file is None) \
                or (self.basis == self.basis_h_ecp and ext_basis_file is None):
            self.gen_basis = False
            self.pseudo_read = False
            return None

        self.gen_basis = True

        # Followings are when Gen is required.
        # case: only light atoms (external file)
        if len(self.atoms_h) == 0:
            gbs = GaussianBasisData(ext_basis_file)
            basis_string = gbs.get_basis(self.atoms_l)
            ecp_string = gbs.get_ecp(self.atoms_l)
            if ecp_string == '':
                self.pseudo_read = False
                return basis_string
            else:
                self.pseudo_read = True
                return basis_string + '\n' + ecp_string

        # case: only heavy atoms (external file)
        if len(self.atoms_l) == 0:
            gbs = GaussianBasisData(ext_basis_h_file)
            basis_string = gbs.get_basis(self.atoms_h)
            ecp_string = gbs.get_ecp(self.atoms_h)
            if ecp_string == '':
                self.pseudo_read = False
                return basis_string
            else:
                self.pseudo_read = True
                return basis_string + '\n' + ecp_string

        # light and heavy atoms; further classification based on external file exists or not.
        # both light and heavy atoms with built-in (but different basis set)
        if (ext_basis_file is None) and (ext_basis_h_file is None):
            self.pseudo_read = True  # It is assumed that built-in set for heavy atoms is ecp-based.
            basis_string = get_gen_basis_string(self.atoms_l, self.basis) \
                           + get_gen_basis_string(self.atoms_h, self.basis_h_ecp)
            ecp_string = get_gen_ecp_string(self.atoms_h, self.basis_h_ecp)
            return basis_string + '\n' + ecp_string

        # both light and heavy atoms call external file
        if (ext_basis_file is not None) and (ext_basis_h_file is not None):
            gbs_l = GaussianBasisData(ext_basis_file)
            gbs_h = GaussianBasisData(ext_basis_h_file)
            basis_string = gbs_l.get_basis(self.atoms_l) + gbs_h.get_basis(self.atoms_h)
            ecp_string = gbs_l.get_ecp(self.atoms_l) + gbs_h.get_ecp(self.atoms_h)
            if ecp_string == '':
                self.pseudo_read = False
                return basis_string
            else:
                self.pseudo_read = True
                return basis_string + '\n' + ecp_string

        # light atoms built-in, heavy atoms external file
        if (ext_basis_file is None) and (ext_basis_h_file is not None):
            gbs_h = GaussianBasisData(ext_basis_h_file)
            basis_string = get_gen_basis_string(self.atoms_l, self.basis)
            basis_string += gbs_h.get_basis(self.atoms_h)
            ecp_string = gbs_h.get_ecp(self.atoms_h)
            if ecp_string == '':
                self.pseudo_read = False
                return basis_string
            else:
                self.pseudo_read = True
                return basis_string + '\n' + ecp_string

        # light atoms external file, heavy atoms built-in
        if (ext_basis_file is not None) and (ext_basis_h_file is None):
            gbs_l = GaussianBasisData(ext_basis_file)
            basis_string = get_gen_basis_string(self.atoms_h, self.basis_h_ecp)
            basis_string += gbs_l.get_basis(self.atoms_l)
            ecp_string = get_gen_ecp_string(self.atoms_h, self.basis_h_ecp)
            ecp_string += gbs_l.get_ecp(self.atoms_l)
            self.pseudo_read = True  # It is assumed that built-in set for heavy atoms is ecp-based.
            return basis_string + '\n' + ecp_string
