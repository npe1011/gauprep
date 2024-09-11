from pathlib import Path
from typing import Union, Tuple, List

from config import ATOM_LIST


def read_gaussian_log(file: Union[str, Path]) -> Tuple[int, int, List[str]]:
    """
    :return: (charge: int, multi: int, structure_data list<str>)
    """

    structure_data = []

    with Path(file).open(mode='r') as f:
        log_data = f.readlines()

        # num_coord, num_charge_multi: starting line number of coordinates or charge/multi (last one)
        for (num, line) in enumerate(log_data):
            if 'Input orientation:' in line:
                num_coord = num
            if 'Standard orientation:' in line:
                num_coord = num
            elif 'Multiplicity =' in line:
                line_charge_multi = line

        # get charge and mult: [Charge =  0 Multiplicity = 1]
        charge = int(line_charge_multi.strip().split()[2])
        multi = int(line_charge_multi.strip().split()[5])

        # starting line of orientation
        i = num_coord + 5
        while log_data[i] and ('------' not in log_data[i]):  # read until blank line or -----
            atom_coord = log_data[i].strip().split()
            atom_label = ATOM_LIST[int(atom_coord[1])]
            coord_x = atom_coord[3]
            coord_y = atom_coord[4]
            coord_z = atom_coord[5]
            structure_data.append(atom_label.ljust(10, ' ') + ' ' + coord_x.rjust(12, ' ') + ' ' +
                                  coord_y.rjust(12, ' ') + ' ' + coord_z.rjust(12, ' ') + '\n')
            i = i + 1

    return charge, multi, structure_data


def read_gaussian_input(file: Union[str, Path]) -> Tuple[int, int, List[str]]:
    """
    :return: (charge: int, multi: int, structure_data list<str>)
    """

    input_data = []  # インプットの全データ
    structure_data = []  # 電荷・多重度を含む構造データ

    with Path(file).open(mode='r', encoding='utf-8') as f:  # inputファイルを開く

        # 前処理
        chk_void = False  # 直前の行が空であったかどうか
        line = f.readline()
        while line:
            line = line.lstrip()  # 先頭の空白を削除。空行の場合は改行も消える。
            if not line:  # 空行だった場合
                if not chk_void:  # かつ直前は空行じゃない場合
                    input_data.append("\n")  # 空行とする
                    chk_void = True
                else:
                    pass  # 直前も空行の場合は無視する
            else:  # 空行じゃない場合
                if line[0] != "!":  # コメント行は無視
                    chk_void = False
                    input_data.append(line)
            line = f.readline()

        # 構造データの抜き出し
        state = 0
        for data_line in input_data:
            if state == 0:  # ルートセクション前
                if data_line[0] == '#':
                    state = 1
            elif state == 1:  # ルートセクション中
                if data_line == '\n':  # 空行が見つかったらstate=2（タイトルセクション）
                    state = 2
            elif state == 2:  # タイトルセクション中
                if data_line == '\n':  # 空行が見つかったらstate=3（電荷・多重度と構造）
                    state = 3
            else:
                if data_line != '\n':
                    if data_line[0:2].upper() != 'LP':  # ローンペアは無視
                        structure_data.append(data_line)
                else:
                    break  # 構造のあとに空行がきたら終わり
        # 構造データの抜き出しここまで-------------------------------------------

    charge, multi = [int(x.strip()) for x in structure_data[0].split()]

    return charge, multi, structure_data[1:]


def read_xyz(file: Union[str, Path]) -> List[List[str]]:
    """
    return list of structure data
    """

    with Path(file).open(mode='r') as f:
        xyz_data = f.readlines()

    structure_data_list = []

    i = 0
    while i < len(xyz_data):
        if xyz_data[i].strip() == '':
            i += 1
            continue
        num_atoms = int(xyz_data[i].strip())
        structure_data = xyz_data[i+2:i+num_atoms+2]
        structure_data_list.append(structure_data)
        i += num_atoms + 2

    return structure_data_list


def read_single_file(file: Union[str, Path]) -> Tuple[int, int, List[str]]:
    """
    Read xyz or Gaussian file and return charge, multi, structure data of the last structure
    :return: (charge: int, multi: int, structure_data list<str>)
    """
    file_type = Path(file).suffix.lstrip('.').lower()
    if file_type in ['xyz']:
        structure_list = read_xyz(file)
        return 0, 1, structure_list[-1]
    elif file_type in ['out', 'log']:
        return read_gaussian_log(file)
    else:
        return read_gaussian_input(file)
