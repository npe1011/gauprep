from pathlib import Path
from typing import Union

from config import ATOM_LIST


def _is_start_line(line: str) -> bool:
    data = line.strip().split()
    if len(data) != 2:
        return False
    return (data[0].capitalize() in ATOM_LIST) and (data[1] == '0')


class GaussianBasisData:
    def __init__(self, file: Union[str, Path]):
        self.file: Path = Path(file).absolute()
        self.basis: dict = dict()
        self.ecp:dict = dict()

        with self.file.open() as f:
            data = f.readlines()

        # Split basis set block and ECP block
        # Skip headers
        start_basis = 0
        for (i, line) in enumerate(data):
            if line.strip().startswith('!') or line.strip() == '':
                continue
            else:
                start_basis = i
                break
        data = data[start_basis:]
        basis_data = []
        end_basis = -1
        # until blank line > basis_data
        for (i, line) in enumerate(data):
            if line.strip() == '':
                end_basis = i
                break
            else:
                basis_data.append(line)
        # After blank line > ecp_data
        if end_basis >= 0:
            ecp_data = data[end_basis+1:]
        else:
            ecp_data = []

        # read basis set data
        current_atom = None
        temp_basis_string = ''
        for line in basis_data:
            if current_atom is None:  # starting line of each atom
                if not _is_start_line(line):
                    raise ValueError('GBS format error. The first line should be atom_name 0.')
                current_atom = line.strip().split()[0].capitalize()
                temp_basis_string += line
            elif line.strip().startswith('****'):  # end line
                temp_basis_string += line
                self.basis[current_atom] = temp_basis_string
                temp_basis_string = ''
                current_atom = None
            else:
                temp_basis_string += line

        # read ECP data
        current_atom = None
        temp_ecp_string = ''
        for line in ecp_data:
            if _is_start_line(line):
                if current_atom is not None:
                    self.ecp[current_atom] = temp_ecp_string
                    temp_ecp_string = ''
                current_atom = line.strip().split()[0].capitalize()
                temp_ecp_string += line
            elif line.strip() == '':  # end with blank line
                break
            else:
                temp_ecp_string += line
        if current_atom is not None:
            self.ecp[current_atom] = temp_ecp_string

    def _get_basis(self, atom):
        atom = atom.capitalize()
        if atom in self.basis:
            return self.basis[atom]
        else:
            raise KeyError('Basis functions for ' + atom + ' are not found in ' + str(self.file) + '.')

    def get_basis(self, atoms):
        basis_string = ''
        for atom in atoms:
            basis_string += self._get_basis(atom.capitalize())
        return basis_string

    def _get_ecp(self, atom):
        atom = atom.capitalize()
        if atom in self.ecp:
            return self.ecp[atom]
        else:
            return None

    def get_ecp(self, atoms):
        ecp_string = ''
        for atom in atoms:
            temp = self._get_ecp(atom.capitalize())
            if temp is not None:
                ecp_string += temp
        return ecp_string
