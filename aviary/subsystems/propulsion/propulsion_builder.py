"""
Define subsystem builder for Aviary core propulsion.

Classes
-------
PropulsionBuilderBase : the interface for a propulsion subsystem builder.

CorePropulsionBuilder : the interface for Aviary's core propulsion subsystem builder
"""

import numpy as np

from aviary.interface.utils.markdown_utils import write_markdown_variable_table
from aviary.subsystems.subsystem_builder_base import SubsystemBuilderBase
from aviary.subsystems.propulsion.propulsion_premission import PropulsionPreMission
from aviary.subsystems.propulsion.propulsion_mission import PropulsionMission
from aviary.variable_info.variables import Aircraft

# NOTE These are currently needed to get around variable hierarchy being class-based.
#      Ideally, an alternate solution to loop through the hierarchy will be created and
#      these can be replaced.
from aviary.utils.preprocessors import _get_engine_variables
from aviary.variable_info.variable_meta_data import _MetaData

_default_name = 'propulsion'


class PropulsionBuilderBase(SubsystemBuilderBase):
    def __init__(self, name=None, meta_data=None):
        if name is None:
            name = _default_name

        super().__init__(name=name, meta_data=meta_data)

    def mission_inputs(self, **kwargs):
        return ['*']

    def mission_outputs(self, **kwargs):
        return ['*']


class CorePropulsionBuilder(PropulsionBuilderBase):
    # code_origin is not necessary for this subsystem, catch with kwargs and ignore
    def __init__(self, name=None, meta_data=None, **kwargs):
        if name is None:
            name = 'core_propulsion'

        super().__init__(name=name, meta_data=meta_data)

    def build_pre_mission(self, aviary_inputs):
        return PropulsionPreMission(aviary_options=aviary_inputs)

    def build_mission(self, num_nodes, aviary_inputs, **kwargs):
        return PropulsionMission(num_nodes=num_nodes, aviary_options=aviary_inputs)

    def get_parameters(self, aviary_inputs=None, phase_info=None):
        num_engine_type = len(aviary_inputs.get_val(Aircraft.Engine.NUM_ENGINES))
        params = {}

        # add all variables from Engine & Nacelle to params
        # TODO this assumes that no new categories are added for custom engine models
        for var in _get_engine_variables():
            if var in aviary_inputs:
                # TODO engine_wing_location
                params[var] = {'shape': (num_engine_type, ), 'static_target': True}

        params = {}  # For now
        params[Aircraft.Engine.SCALE_FACTOR] = {'shape': (num_engine_type, ),
                                                'static_target': True}
        return params

    def report(self, prob, reports_folder, **kwargs):
        """
        Generate the report for Aviary core propulsion analysis

        Parameters
        ----------
        prob : AviaryProblem
            The AviaryProblem that will be used to generate the report
        reports_folder : Path
            Location of the subsystems_report folder this report will be placed in
        """
        filename = self.name + '.md'
        filepath = reports_folder / filename

        propulsion_outputs = [Aircraft.Propulsion.TOTAL_NUM_ENGINES,
                              Aircraft.Propulsion.TOTAL_SCALED_SLS_THRUST]

        with open(filepath, mode='w') as f:
            f.write('# Propulsion')
            write_markdown_variable_table(f, prob, propulsion_outputs, self.meta_data)
            f.write('\n## Engines')

        # each engine can append to this file
        kwargs['meta_data'] = self.meta_data
        for engine in prob.aviary_inputs.get_val('engine_models'):
            engine.report(prob, filepath, **kwargs)
