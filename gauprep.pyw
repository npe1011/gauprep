import os
import sys
import configparser
import glob
from pathlib import Path
from typing import Union

import wx
from wx import xrc

APP_DIR = (os.path.dirname(os.path.abspath(__file__)))
sys.path.append(APP_DIR)

from gauprep import structure_reader
from gauprep.gaussian_input import GaussianInputData
import config

# Notes:
# ${NAME} ${NUMBER} are replaced in the interface (here)
# ${FILENAME} ${GEN} are replaced in the GaussianInputData class


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, file_list):
        # single job
        if self.window.notebook_general.GetSelection() == 0:
            self.load_to_single(file_list)
        # batch job
        elif self.window.notebook_general.GetSelection() == 1:
            self.load_to_batch(file_list)
        # series job
        elif self.window.notebook_general.GetSelection() == 2:
            self.load_to_series(file_list)
        return True

    def load_to_single(self, file_list):
        for file in file_list:
            if os.path.splitext(file)[1] == '.sset':
                self.window.file_load(file)
            else:
                self.window.text_ctrl_structure_file.SetValue(file)
                self.window.set_output_file_auto()
                self.window.set_title_auto()

    def load_to_batch(self, file_list):
        output_file_list = (self.window.text_ctrl_batch_file_list.GetValue()).split('\n')
        expanded_file_list = self.expand_file_list(file_list)

        for file in expanded_file_list:
            ext = os.path.splitext(os.path.basename(file))[1]
            if ext == '.sset':
                self.window.file_load(file)
            else:
                output_file_list.append(file)

        self.window.text_ctrl_batch_file_list.SetValue('\n'.join(output_file_list))
        self.window.clean_up_batch_file_list()

    def load_to_series(self, file_list):
        for file in file_list:
            if os.path.splitext(file)[1] == '.sset':
                self.window.file_load(file)
            else:
                self.window.text_ctrl_series_xyz_file.SetValue(file)
                self.window.set_series_output_file_auto()
                self.window.set_series_title_auto()

    @staticmethod
    def expand_file_list(file_list):
        """
        ディレクトリを含むファイル名のリストが与えられたとき、ディレクトリ内部も検索して、それ以下にある全ファイルリストを返す
        """
        expanded_list = []

        for file in file_list:
            if os.path.isdir(file):  # ディレクトリが与えられた場合
                glob_list = glob.glob(file + "/**", recursive=True)  # ディレクトリ内の全ファイル・ディレクトリリストを取得（子ディレクトリも検索）
                # 全リストのうち、ファイルであるものをexpanded_listに追加する
                for f in glob_list:
                    if os.path.isfile(f):
                        expanded_list.append(f)

            else:  # ファイルの場合はそのまま追加
                expanded_list.append(file)

        return expanded_list


class GauprepApp(wx.App):

    def OnInit(self):
        self.init_frame()
        return True

    def init_frame(self):
        self.res = xrc.XmlResource(APP_DIR + '/wxgui/gui.xrc')
        self.frame = self.res.LoadFrame(None, 'frame')
        self.frame.SetSize((800, 800))
        self.load_controls()
        self.init_controls()
        # self.check_controls()

        # Drop targe settings
        dt = MyFileDropTarget(self)
        self.frame.SetDropTarget(dt)

        # Bind event handlers
        self.set_events()

        # menu
        self.create_menu_bar()

        # load previous setting file
        self.load_init_file()

        # initialize batch settings
        self.reset_batch_settings()

        # redirect
        sys.stdout = self.text_ctrl_log
        sys.stderr = self.text_ctrl_log

        self.frame.Show()

    def load_controls(self):
        # General
        self.notebook_general: wx.Notebook = xrc.XRCCTRL(self.frame, 'notebook_general')

        # General: single job
        self.text_ctrl_structure_file: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_structure_file')
        self.button_structure_file: wx.Button = xrc.XRCCTRL(self.frame, 'button_structure_file')
        self.text_ctrl_output_file: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_output_file')
        self.button_output_file_auto: wx.Button = xrc.XRCCTRL(self.frame, 'button_output_file_auto')
        self.text_ctrl_title: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_title')
        self.button_title_auto: wx.Button = xrc.XRCCTRL(self.frame, 'button_title_auto')

        # General: batch job
        self.text_ctrl_batch_file_list: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_batch_file_list')
        self.text_ctrl_batch_prefix: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_batch_prefix')
        self.text_ctrl_batch_suffix: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_batch_suffix')
        self.text_ctrl_batch_title: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_batch_title')
        self.checkbox_batch_overwrite: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_batch_overwrite')
        self.button_batch_reset: wx.Button = xrc.XRCCTRL(self.frame, 'button_batch_reset')

        # General series job
        self.text_ctrl_series_charge: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_series_charge')
        self.text_ctrl_series_multiplicity: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_series_multiplicity')
        self.text_ctrl_series_xyz_file: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_series_xyz_file')
        self.text_ctrl_series_output_file_prefix: wx.TextCtrl = xrc.XRCCTRL(self.frame,
                                                                            'text_ctrl_series_output_file_prefix')
        self.text_ctrl_series_output_file_suffix: wx.TextCtrl = xrc.XRCCTRL(self.frame,
                                                                            'text_ctrl_series_output_file_suffix')
        self.text_ctrl_series_title: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_series_title')
        self.button_series_xyz_file: wx.Button = xrc.XRCCTRL(self.frame, 'button_series_xyz_file')
        self.button_series_output_file_auto: wx.Button = xrc.XRCCTRL(self.frame, 'button_series_output_file_auto')
        self.button_series_title_auto: wx.Button = xrc.XRCCTRL(self.frame, 'button_series_title_auto')

        # Link0
        self.text_ctrl_cpu_cores: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_cpu_cores')
        self.text_ctrl_memory: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_memory')

        # Model
        self.choice_method: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_method')
        self.choice_basis: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_basis')
        self.choice_basis_h_ecp: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_basis_h_ecp')
        self.checkbox_ecp_for_3d: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_ecp_for_3d')
        self.radio_box_solvation: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_solvation')
        self.choice_solvent: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_solvent')
        self.radio_box_dispersion: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_dispersion')
        self.checkbox_dispersion_ext: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_dispersion_ext')
        self.checkbox_nosymm: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_nosymm')
        self.checkbox_guessmix: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_guessmix')
        self.checkbox_stableopt: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_stableopt')

        # Job
        self.notebook_job: wx.Notebook = xrc.XRCCTRL(self.frame, 'notebook_job')

        # Job: SP/FREQ
        self.checkbox_sp_run_freq: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_sp_run_freq')
        self.button_sp_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_sp_output')

        # Job: OPT/TS
        self.radio_box_opt_job_type: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_opt_job_type')
        self.choice_opt_algorithm: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_opt_algorithm')
        self.choice_opt_convergence: wx.Choice = xrc.XRCCTRL(self.frame, 'choice_opt_convergence')
        self.text_ctrl_opt_maxcycle: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_opt_maxcycle')
        self.text_ctrl_opt_maxstep: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_opt_maxstep')
        self.text_ctrl_opt_calcfc: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_opt_calcfc')
        self.text_ctrl_opt_modredundant: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_opt_modredundant')
        self.button_opt_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_opt_output')

        # Job: IRC
        self.radio_box_irc_algorithm: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_irc_algorithm')
        self.radio_box_irc_direction: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_irc_direction')
        self.text_ctrl_irc_maxpoints: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_irc_maxpoints')
        self.text_ctrl_irc_stepsize: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_irc_stepsize')
        self.text_ctrl_irc_maxcyc: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_irc_maxcyc')
        self.text_ctrl_irc_calcfc_predictor: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_irc_calcfc_predictor')
        self.text_ctrl_irc_calcfc_corrector: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_irc_calcfc_corrector')
        self.button_irc_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_irc_output')

        # Job: WFX
        self.button_wfx_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_wfx_output')

        # Job: NBO
        self.radio_box_nbo_version: wx.RadioBox = xrc.XRCCTRL(self.frame, 'radio_box_nbo_version')
        self.checkbox_nbo_save: wx.CheckBox = xrc.XRCCTRL(self.frame, 'checkbox_nbo_save')
        self.check_list_box_nbo_keywords: wx.CheckListBox = xrc.XRCCTRL(self.frame, 'check_list_box_nbo_keywords')
        self.text_ctrl_nbo_additional_keywords: wx.TextCtrl = xrc.XRCCTRL(self.frame,
                                                                          'text_ctrl_nbo_additional_keywords')
        self.button_nbo_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_nbo_output')

        # Job: Any
        self.text_ctrl_any_job_input: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_any_job_input')
        self.button_any_output: wx.Button = xrc.XRCCTRL(self.frame, 'button_any_output')

        # Log
        self.text_ctrl_log: wx.TextCtrl = xrc.XRCCTRL(self.frame, 'text_ctrl_log')

    def init_controls(self):
        # set choice controls from setting file
        self.append_items_from_file(self.choice_method, config.METHOD_FILE)
        self.append_items_from_file(self.choice_basis, config.BASIS_FILE)
        self.append_items_from_file(self.choice_basis_h_ecp, config.BASIS_H_ECP_file)
        self.append_items_from_file(self.choice_solvent, config.SOLVENT_FILE)
        self.append_items_from_file(self.choice_opt_convergence, config.OPT_CONVERGENCE_FILE)
        self.append_items_from_file(self.choice_opt_algorithm, config.OPT_ALGORITHM_FILE)

    def check_controls(self):
        assert self.notebook_general is not None
        assert self.text_ctrl_structure_file is not None
        assert self.button_structure_file is not None
        assert self.text_ctrl_output_file is not None
        assert self.button_output_file_auto is not None
        assert self.text_ctrl_title is not None
        assert self.button_title_auto is not None
        assert self.text_ctrl_batch_file_list is not None
        assert self.text_ctrl_batch_prefix is not None
        assert self.text_ctrl_batch_suffix is not None
        assert self.text_ctrl_batch_title is not None
        assert self.checkbox_batch_overwrite is not None
        assert self.button_batch_reset is not None
        assert self.text_ctrl_series_charge is not None
        assert self.text_ctrl_series_multiplicity is not None
        assert self.text_ctrl_series_xyz_file is not None
        assert self.text_ctrl_series_output_file_prefix is not None
        assert self.text_ctrl_series_output_file_suffix is not None
        assert self.text_ctrl_series_title is not None
        assert self.button_series_xyz_file is not None
        assert self.button_series_output_file_auto is not None
        assert self.button_series_title_auto is not None
        assert self.text_ctrl_cpu_cores is not None
        assert self.text_ctrl_memory is not None
        assert self.choice_method is not None
        assert self.choice_basis is not None
        assert self.choice_basis_h_ecp is not None
        assert self.checkbox_ecp_for_3d is not None
        assert self.radio_box_solvation is not None
        assert self.choice_solvent is not None
        assert self.radio_box_dispersion is not None
        assert self.checkbox_dispersion_ext is not None
        assert self.checkbox_nosymm is not None
        assert self.checkbox_guessmix is not None
        assert self.checkbox_stableopt is not None
        assert self.notebook_job is not None
        assert self.checkbox_sp_run_freq is not None
        assert self.button_sp_output is not None
        assert self.radio_box_opt_job_type is not None
        assert self.choice_opt_algorithm is not None
        assert self.choice_opt_convergence is not None
        assert self.text_ctrl_opt_maxcycle is not None
        assert self.text_ctrl_opt_maxstep is not None
        assert self.text_ctrl_opt_calcfc is not None
        assert self.text_ctrl_opt_modredundant is not None
        assert self.button_opt_output is not None
        assert self.radio_box_irc_algorithm is not None
        assert self.radio_box_irc_direction is not None
        assert self.text_ctrl_irc_maxpoints is not None
        assert self.text_ctrl_irc_stepsize is not None
        assert self.text_ctrl_irc_maxcyc is not None
        assert self.text_ctrl_irc_calcfc_predictor is not None
        assert self.text_ctrl_irc_calcfc_corrector is not None
        assert self.button_irc_output is not None
        assert self.button_wfx_output is not None
        assert self.radio_box_nbo_version is not None
        assert self.checkbox_nbo_save is not None
        assert self.check_list_box_nbo_keywords is not None
        assert self.text_ctrl_nbo_additional_keywords is not None
        assert self.button_nbo_output is not None
        assert self.text_ctrl_any_job_input is not None
        assert self.button_any_output is not None
        assert self.text_ctrl_log is not None

    def set_events(self):
        self.button_structure_file.Bind(wx.EVT_BUTTON, self.on_button_structure_file)
        self.button_output_file_auto.Bind(wx.EVT_BUTTON, self.on_button_output_file_auto)
        self.button_series_xyz_file.Bind(wx.EVT_BUTTON, self.on_button_series_xyz_file)
        self.button_series_output_file_auto.Bind(wx.EVT_BUTTON, self.on_button_series_output_file_auto)
        self.button_series_title_auto.Bind(wx.EVT_BUTTON, self.on_button_series_title_auto)
        self.button_title_auto.Bind(wx.EVT_BUTTON, self.on_button_title_auto)
        self.button_sp_output.Bind(wx.EVT_BUTTON, self.on_button_sp_output)
        self.button_opt_output.Bind(wx.EVT_BUTTON, self.on_button_opt_output)
        self.button_irc_output.Bind(wx.EVT_BUTTON, self.on_button_irc_output)
        self.button_batch_reset.Bind(wx.EVT_BUTTON, self.on_button_batch_reset)
        self.button_wfx_output.Bind(wx.EVT_BUTTON, self.on_button_wfx_output)
        self.button_nbo_output.Bind(wx.EVT_BUTTON, self.on_button_nbo_output)
        self.button_any_output.Bind(wx.EVT_BUTTON, self.on_button_any_output)

        self.frame.Bind(wx.EVT_CLOSE, self.on_exit)

    @staticmethod
    def append_items_from_file(target, file: Union[str, Path]):
        """
        Set items to control which has Append method.
        """
        with open(file, 'r') as f:
            line = f.readline().strip()
            while line:
                if line == '':
                    continue
                target.Append(line)
                line = f.readline().strip()

    def create_menu_bar(self):
        # menu bar
        menu_bar = wx.MenuBar()
        file = wx.Menu()
        menu_open = file.Append(11, "&Open\tCtrl+O")
        menu_save = file.Append(12, "&Save\tCtrl+S")
        menu_load_default = file.Append(13, "&Load Default\tCtrl+D")
        menu_bar.Append(file, "&File")
        self.frame.SetMenuBar(menu_bar)

        # event set for menus
        self.Bind(wx.EVT_MENU, self.on_menu_open, menu_open)
        self.Bind(wx.EVT_MENU, self.on_menu_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_menu_load_default, menu_load_default)

    def logging(self, message):
        log_string = (''.join(message)).rstrip()
        self.text_ctrl_log.write(log_string + '\n')

    def file_load(self, file: Union[str, Path]):
        """
        Set controls from config file
        """
        setdata = configparser.ConfigParser()
        setdata.read(file)

        self.text_ctrl_cpu_cores.SetValue(setdata.get('Link0', 'cpu_cores'))
        self.text_ctrl_memory.SetValue(setdata.get('Link0', 'memory'))

        self.choice_method.SetStringSelection(setdata.get('Model', 'method'))
        self.choice_basis.SetStringSelection(setdata.get('Model', 'basis'))
        self.choice_basis_h_ecp.SetStringSelection(setdata.get('Model', 'basis_h_ecp'))
        self.checkbox_ecp_for_3d.SetValue(setdata.getboolean('Model', 'ecp_for_3d'))
        self.radio_box_solvation.SetStringSelection(setdata.get('Model', 'solvation'))
        self.choice_solvent.SetStringSelection(setdata.get('Model', 'solvent'))
        self.radio_box_dispersion.SetStringSelection(setdata.get('Model', 'dispersion'))
        self.checkbox_dispersion_ext.SetValue(setdata.getboolean('Model', 'dispersion_ext'))
        self.checkbox_nosymm.SetValue(setdata.getboolean('Model', 'nosymm'))
        self.checkbox_guessmix.SetValue(setdata.getboolean('Model', 'guessmix'))
        self.checkbox_stableopt.SetValue(setdata.getboolean('Model', 'stableopt'))

        self.notebook_job.SetSelection(setdata.getint('Job', 'selection'))

        self.checkbox_sp_run_freq.SetValue(setdata.getboolean('SP', 'run_freq'))

        self.radio_box_opt_job_type.SetStringSelection(setdata.get('Opt', 'job_type'))
        self.choice_opt_convergence.SetStringSelection(setdata.get('Opt', 'convergence'))
        self.text_ctrl_opt_maxcycle.SetValue(setdata.get('Opt', 'maxcycle'))
        self.text_ctrl_opt_maxstep.SetValue(setdata.get('Opt', 'maxstep'))
        self.text_ctrl_opt_calcfc.SetValue(setdata.get('Opt', 'calcfc'))
        self.choice_opt_algorithm.SetStringSelection(setdata.get('Opt', 'algorithm'))
        self.text_ctrl_opt_modredundant.SetValue(setdata.get('Opt', 'modredundant'))

        self.radio_box_irc_algorithm.SetStringSelection(setdata.get('IRC', 'algorithm'))
        self.radio_box_irc_direction.SetStringSelection(setdata.get('IRC', 'direction'))
        self.text_ctrl_irc_maxpoints.SetValue(setdata.get('IRC', 'maxpoints'))
        self.text_ctrl_irc_stepsize.SetValue(setdata.get('IRC', 'stepsize'))
        self.text_ctrl_irc_maxcyc.SetValue(setdata.get('IRC', 'maxcyc'))
        self.text_ctrl_irc_calcfc_predictor.SetValue(setdata.get('IRC', 'calcfc_predictor'))
        self.text_ctrl_irc_calcfc_corrector.SetValue(setdata.get('IRC', 'calcfc_corrector'))

        self.radio_box_nbo_version.SetStringSelection(setdata.get('NBO', 'version'))
        self.checkbox_nbo_save.SetValue(setdata.getboolean('NBO', 'save_in_chk'))
        self.check_list_box_nbo_keywords.SetCheckedStrings(setdata.get('NBO', 'keywords').split())
        self.text_ctrl_nbo_additional_keywords.SetValue(setdata.get('NBO', 'additional_keywords'))

        self.text_ctrl_any_job_input.SetValue(setdata.get('ANY', 'job_input'))

        self.logging('Settings were loaded from file: ' + str(Path(file).absolute()))

    def file_save(self, file: Union[str, Path]):
        """
        save config file from controls
        """
        setdata = configparser.ConfigParser()

        setdata.add_section('Link0')
        setdata.set('Link0', 'cpu_cores', self.text_ctrl_cpu_cores.GetValue())
        setdata.set('Link0', 'memory', self.text_ctrl_memory.GetValue())

        setdata.add_section('Model')
        setdata.set('Model', 'method', self.choice_method.GetStringSelection())
        setdata.set('Model', 'basis', self.choice_basis.GetStringSelection())
        setdata.set('Model', 'basis_h_ecp', self.choice_basis_h_ecp.GetStringSelection())
        setdata.set('Model', 'ecp_for_3d', str(self.checkbox_ecp_for_3d.GetValue()))
        setdata.set('Model', 'solvation', self.radio_box_solvation.GetStringSelection())
        setdata.set('Model', 'solvent', self.choice_solvent.GetStringSelection())
        setdata.set('Model', 'dispersion', self.radio_box_dispersion.GetStringSelection())
        setdata.set('Model', 'dispersion_ext', str(self.checkbox_dispersion_ext.GetValue()))
        setdata.set('Model', 'nosymm', str(self.checkbox_nosymm.GetValue()))
        setdata.set('Model', 'guessmix', str(self.checkbox_guessmix.GetValue()))
        setdata.set('Model', 'stableopt', str(self.checkbox_stableopt.GetValue()))

        setdata.add_section('Job')
        setdata.set('Job', 'selection', str(self.notebook_job.GetSelection()))

        setdata.add_section('SP')
        setdata.set('SP', 'run_freq', str(self.checkbox_sp_run_freq.GetValue()))

        setdata.add_section('Opt')
        setdata.set('Opt', 'job_type', self.radio_box_opt_job_type.GetStringSelection())
        setdata.set('Opt', 'convergence', self.choice_opt_convergence.GetStringSelection())
        setdata.set('Opt', 'maxcycle', self.text_ctrl_opt_maxcycle.GetValue())
        setdata.set('Opt', 'maxstep', self.text_ctrl_opt_maxstep.GetValue())
        setdata.set('Opt', 'calcfc', self.text_ctrl_opt_calcfc.GetValue())
        setdata.set('Opt', 'algorithm', self.choice_opt_algorithm.GetStringSelection())
        setdata.set('Opt', 'modredundant', self.text_ctrl_opt_modredundant.GetValue())

        setdata.add_section('IRC')
        setdata.set('IRC', 'algorithm', self.radio_box_irc_algorithm.GetStringSelection())
        setdata.set('IRC', 'direction', self.radio_box_irc_direction.GetStringSelection())
        setdata.set('IRC', 'maxpoints', self.text_ctrl_irc_maxpoints.GetValue())
        setdata.set('IRC', 'stepsize', self.text_ctrl_irc_stepsize.GetValue())
        setdata.set('IRC', 'maxcyc',  self.text_ctrl_irc_maxcyc.GetValue())
        setdata.set('IRC', 'calcfc_predictor', self.text_ctrl_irc_calcfc_predictor.GetValue())
        setdata.set('IRC', 'calcfc_corrector', self.text_ctrl_irc_calcfc_corrector.GetValue())

        setdata.add_section('NBO')
        setdata.set('NBO', 'version', self.radio_box_nbo_version.GetStringSelection())
        setdata.set('NBO', 'save_in_chk', str(self.checkbox_nbo_save.GetValue()))
        setdata.set('NBO', 'keywords', ' '.join(self.check_list_box_nbo_keywords.GetCheckedStrings()))
        setdata.set('NBO', 'additional_keywords', self.text_ctrl_nbo_additional_keywords.GetValue().strip())

        setdata.add_section('ANY')
        setdata.set('ANY', 'job_input', self.text_ctrl_any_job_input.GetValue().strip())

        with open(file, 'w') as f:
            setdata.write(f)

        self.logging('Current settings were saved in file: ' + str(Path(file).absolute()))

    def load_init_file(self):
        """
        read previous set file
        """
        try:
            self.file_load(config.PREVIOUS_SET_FILE)
        except Exception as e:
            self.logging(e.args)
        else:
            return

        # in case error occurs when previous file is read > read default file
        try:
            self.file_load(config.DEFAULT_SET_FILE)
        except Exception as e:
            self.logging(e.args)
        else:
            return

        # here, initialization failed.
        self.logging('Parameter initialization failed.')
        
    def select_structure_file(self, event):
        dialog = wx.FileDialog(None, 'Select input file',
                               wildcard='Gaussian job or log files (*.gjf;*.gjc;*.com;*.log;*.out)|*.gjf;*.gjc;*.com;'
                                        '*.log;*.out|All files (*.*)|*.*',
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            self.text_ctrl_structure_file.SetValue(filename)
        dialog.Destroy()

    def set_output_file_auto(self):
        self.text_ctrl_output_file.SetValue('${NAME}.gjf')

    def set_title_auto(self):
        self.text_ctrl_title.SetValue('${FILENAME} ${GEN}')

    def set_series_output_file_auto(self):
        self.text_ctrl_series_output_file_prefix.SetValue('${NAME}_')
        self.text_ctrl_series_output_file_suffix.SetValue('')

    def set_series_title_auto(self):
        self.text_ctrl_series_title.SetValue('${FILENAME} ${GEN}')

    def reset_batch_settings(self):
        self.text_ctrl_batch_file_list.SetValue('')
        self.text_ctrl_batch_prefix.SetValue('')
        self.text_ctrl_batch_suffix.SetValue('')
        self.text_ctrl_batch_title.SetValue('${FILENAME} ${GEN}')
        self.checkbox_batch_overwrite.SetValue(True)

    def clean_up_batch_file_list(self):
        """
        check batch file list and remove non-existing files and duplicated files
        """
        # list with split lines
        file_list = (self.text_ctrl_batch_file_list.GetValue()).split('\n')

        new_file_list = []
        for file in file_list:
            if (file not in new_file_list) and os.path.exists(file):
                new_file_list.append(file)

        # Reload control
        self.text_ctrl_batch_file_list.SetValue('\n'.join(new_file_list))

    def output(self, job_type):
        if self.notebook_general.GetSelection() == 0:  # single job
            self.output_single(job_type=job_type)
        elif self.notebook_general.GetSelection() == 1:  # batch
            self.output_batch(job_type=job_type)
        elif self.notebook_general.GetSelection() == 2:  # series
            self.output_series(job_type=job_type)

    def output_single(self, job_type):

        # in case no input file
        if self.text_ctrl_structure_file.GetValue().strip() == '':
            self.logging('Structure file is not given.\n')
            return
        if not os.path.exists(self.text_ctrl_structure_file.GetValue()):
            self.logging('File: ' + self.text_ctrl_structure_file.GetValue() + ' does not exist.\n')
            return

        # Get control data
        input_file = Path(self.text_ctrl_structure_file.GetValue())
        name = input_file.stem
        title = self.text_ctrl_title.GetValue().replace('${NAME}', name)
        charge, mult, structure = structure_reader.read_single_file(input_file)
        gid = self.generate_gaussian_input_data_object(title=title, charge=charge, multiplicity=mult,
                                                       structure=structure, job_type=job_type)

        # output dir is where input_file is.
        output_dir = input_file.parent
        # output file name
        if self.text_ctrl_output_file.GetValue().strip() == '':
            output_name = 'default.gjf'
        else:
            output_name = self.text_ctrl_output_file.GetValue()
        output_name = output_name.replace('${NAME}', name)  # NAMEの置き換え
        output_file = output_dir / output_name

        # Overwrite check
        if output_file.exists():
            msgbox = wx.MessageDialog(None,
                                      'Following file already exists. Overwrite?\n' + str(output_file),
                                      'Overwrite?', style=wx.YES_NO)
            if msgbox.ShowModal() == wx.ID_YES:
                msgbox.Destroy()
            else:
                msgbox.Destroy()
                self.logging('Canceled.\n')
                return

        gid.output_file(output_file)
        self.logging('Generated file: ' + str(output_file))

    def output_batch(self, job_type):
        file_list = [x.strip() for x in self.text_ctrl_batch_file_list.GetValue().split('\n')]  # split lines + strip()
        file_list = [x for x in file_list if x != '']  # remove blank lines

        count = 0
        for file in file_list:

            file = Path(file)
            if not file.exists():
                self.logging('File: ' + str(file) + ' does not exist.\n')
                continue

            # output names
            name = file.stem
            prefix = self.text_ctrl_batch_prefix.GetValue().strip()
            suffix = self.text_ctrl_batch_suffix.GetValue().strip()
            output_file_name = prefix + name + suffix + '.gjf'
            output_file_name = output_file_name.replace('${NAME}', name)
            output_dir = file.parent
            output_file = output_dir / output_file_name

            # title
            title = self.text_ctrl_batch_title.GetValue()
            title = title.replace('${NAME}', name)

            # get from controls
            charge, mult, structure = structure_reader.read_single_file(file)
            gid = self.generate_gaussian_input_data_object(title=title, charge=charge, multiplicity=mult,
                                                           structure=structure, job_type=job_type)

            # Overwrite check
            if output_file.exists() and self.checkbox_batch_overwrite.GetValue():
                msgbox = wx.MessageDialog(None,
                                          'Following file already exists. Overwrite?\n' + str(output_file),
                                          'Overwrite?', style=wx.YES_NO)
                if msgbox.ShowModal() == wx.ID_YES:
                    msgbox.Destroy()
                else:
                    msgbox.Destroy()
                    self.logging('Canceled.\n')
                    continue

            gid.output_file(output_file)
            self.logging('Generated file: ' + str(output_file))
            count += 1

        self.logging('Total ' + str(count) + ' files were generated.')

    def output_series(self, job_type):
        if self.text_ctrl_series_xyz_file.GetValue().strip() == '':
            self.logging('xyz file is not given.\n')
            return
        if not os.path.exists(self.text_ctrl_series_xyz_file.GetValue()):
            self.logging('File: ' + self.text_ctrl_series_xyz_file.GetValue() + ' does not exist.\n')
            return

        input_file = Path(self.text_ctrl_series_xyz_file.GetValue())
        name = input_file.stem
        output_dir = input_file.parent
        structure_list = structure_reader.read_xyz(input_file)
        number_digit = max(3, len(str(len(structure_list))))

        count = 0
        for i, structure in enumerate(structure_list):
            number = str(i + 1).zfill(number_digit)
            # output names
            prefix = self.text_ctrl_series_output_file_prefix.GetValue().strip()
            suffix = self.text_ctrl_series_output_file_suffix.GetValue().strip()
            output_file_name = prefix + number + suffix + '.gjf'
            output_file_name = output_file_name.replace('${NAME}', name).replace('${NUMBER}', number)
            output_file = output_dir / output_file_name
            # titles
            title = self.text_ctrl_series_title.GetValue()
            title = title.replace('${NAME}', name).replace('${NUMBER}', number)
            # charge/mult
            charge = int(self.text_ctrl_series_charge.GetValue().strip())
            mult = int(self.text_ctrl_series_multiplicity.GetValue().strip())
            gid = self.generate_gaussian_input_data_object(title=title, charge=charge, multiplicity=mult,
                                                           structure=structure, job_type=job_type)
            gid.output_file(output_file)
            self.logging('Generated file: ' + str(output_file))
            count += 1

        self.logging('Total ' + str(count) + ' files were generated.')

    def generate_gaussian_input_data_object(self, title, charge, multiplicity, structure, job_type) -> GaussianInputData:

        gid = GaussianInputData(charge, multiplicity, structure)
        gid.job_type = job_type  # SP, Opt, Opt+Freq, TS, IRC, WFX, NBO, ANY
        gid.title = title

        # read from controls
        gid.memory = self.text_ctrl_memory.GetValue()
        gid.n_proc = self.text_ctrl_cpu_cores.GetValue()
        gid.method = self.choice_method.GetStringSelection()  # functional name or HF, MP2
        gid.basis = self.choice_basis.GetStringSelection()  # basis name
        gid.basis_h_ecp = self.choice_basis_h_ecp.GetStringSelection()  # basis name
        gid.ecp_for_3d = self.checkbox_ecp_for_3d.GetValue()  # True for apply ECP basis set to 3d metal row atoms
        gid.nosymm = self.checkbox_nosymm.GetValue()  # True for add nosymm keyword
        gid.guess_mix = self.checkbox_guessmix.GetValue()  # True for add guess=mix
        gid.first_stable_check = self.checkbox_stableopt.GetValue()  # True for first stable=opt (multi job or sp)

        gid.solvation = self.radio_box_solvation.GetStringSelection()  # none, PCM, CPCM, SMD
        gid.solvent = self.choice_solvent.GetStringSelection()  # solvent name

        gid.dispersion = self.radio_box_dispersion.GetStringSelection()  # none, GD3, GD3BJ, D2
        gid.dispersion_external_param = self.checkbox_dispersion_ext.GetValue()  # True for read external files

        gid.opt_convergence = self.choice_opt_convergence.GetStringSelection()  # loose, default, tight, verytight
        gid.opt_maxcycle = self.text_ctrl_opt_maxcycle.GetValue()  # '',  int > 0
        gid.opt_maxstep = self.text_ctrl_opt_maxstep.GetValue()  # '', int > 0
        gid.opt_calcfc = self.text_ctrl_opt_calcfc.GetValue()  # '', 0 for calcfc, 1 for calcall, int > 1 for recalcfc
        gid.opt_algorithm = self.choice_opt_algorithm.GetStringSelection()  # default, GDIIS, Newton
        gid.opt_modredundant = self.text_ctrl_opt_modredundant.GetValue()  # modredundant sections

        gid.irc_algorithm = self.radio_box_irc_algorithm.GetStringSelection()  # HPC, EulerPC, LQA
        gid.irc_direction = self.radio_box_irc_direction.GetStringSelection()  # both, forward, reverse
        gid.irc_maxpoints = self.text_ctrl_irc_maxpoints.GetValue()  # '', int > 0
        gid.irc_stepsize = self.text_ctrl_irc_stepsize.GetValue()  # '', int > 0
        gid.irc_maxcyc = self.text_ctrl_irc_maxcyc.GetValue()  # '', int > 0
        gid.irc_calcfc_predictor = self.text_ctrl_irc_calcfc_predictor.GetValue()  # '', int > 0
        gid.irc_calcfc_corrector = self.text_ctrl_irc_calcfc_corrector.GetValue()  # '', int > 0

        gid.nbo_version = self.radio_box_nbo_version.GetStringSelection()
        gid.nbo_save = self.checkbox_nbo_save.GetValue()
        nbo_keywords = list(self.check_list_box_nbo_keywords.GetCheckedStrings())
        nbo_keywords.extend(self.text_ctrl_nbo_additional_keywords.GetValue().strip().split())
        gid.nbo_keywords = nbo_keywords

        gid.any_job_input = self.text_ctrl_any_job_input.GetValue().strip()

        return gid

    # Followings are event handlers
    def on_button_structure_file(self, event):
        dialog = wx.FileDialog(None, 'Select structure file',
                               wildcard='Gaussian job/log file or xyz file (*.gjf;*.gjc;*.com;*.log;*.out;*.xyz)|*.gjf;'
                                        '*.gjc;*.com;*.log;*.out;*.xyz|All files (*.*)|*.*',
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            self.text_ctrl_structure_file.SetValue(file)
            self.set_output_file_auto()
            self.set_title_auto()
        dialog.Destroy()

    def on_button_output_file_auto(self, event):
        self.set_output_file_auto()

    def on_button_title_auto(self, event):
        self.set_title_auto()

    def on_button_series_xyz_file(self, event):
        dialog = wx.FileDialog(None, 'Select xyz file',
                               wildcard='xyz file (*.xyz)|All files (*.*)|*.*',
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            self.text_ctrl_series_xyz_file.SetValue(file)
            self.set_series_output_file_auto()
            self.set_series_title_auto()
        dialog.Destroy()

    def on_button_series_output_file_auto(self, event):
        self.set_series_output_file_auto()

    def on_button_series_title_auto(self, event):
        self.set_series_title_auto()

    def on_button_batch_reset(self, event):
        self.reset_batch_settings()

    def on_button_sp_output(self, event):
        if self.checkbox_sp_run_freq.GetValue():
            job_type = 'FREQ'
        else:
            job_type = 'SP'
        self.output(job_type=job_type)

    def on_button_opt_output(self, event):
        job_type = self.radio_box_opt_job_type.GetStringSelection()
        self.output(job_type=job_type)

    def on_button_irc_output(self, event):
        self.output(job_type='IRC')

    def on_button_wfx_output(self, event):
        self.output(job_type='WFX')

    def on_button_nbo_output(self, event):
        self.output(job_type='NBO')

    def on_button_any_output(self, event):
        self.output(job_type='ANY')

    def on_menu_open(self, event):
        dialog = wx.FileDialog(None, 'Select user set file',
                               wildcard='Set files (*.sset)|*.sset|All files (*.*)|*.*',
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            self.file_load(file)
        dialog.Destroy()

    def on_menu_save(self, event):
        dialog = wx.FileDialog(None, 'Input file name',
                               wildcard='Set files (*.sset)|*.sset|All files (*.*)|*.*',
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            dialog.Destroy()
        else:
            dialog.Destroy()
            return

        # Overwrite check
        if os.path.exists(file):
            msgbox = wx.MessageDialog(None, 'File already exists. Overwrite?', 'Overwrite?', style=wx.YES_NO)
            overwrite = msgbox.ShowModal()
            if overwrite == wx.ID_YES:
                msgbox.Destroy()
            else:
                msgbox.Destroy()
                return

        self.file_save(file)

    def on_menu_load_default(self, event):
        self.file_load(config.DEFAULT_SET_FILE)

    def on_exit(self, event):
        try:
            self.file_save(config.PREVIOUS_SET_FILE)
        finally:
            wx.Exit()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = GauprepApp(False)
    app.MainLoop()
