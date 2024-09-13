from packaging import version
import warnings

import openmdao
import openmdao.api as om

from aviary.utils.base_classes import AviaryGroup
from aviary.variable_info.variables import Aircraft, Mission
from aviary.utils.aviary_values import AviaryValues
from aviary.variable_info.variable_meta_data import _MetaData
from aviary.variable_info.functions import override_aviary_vars

use_new_openmdao_syntax = version.parse(openmdao.__version__) >= version.parse("3.28")


class CorePreMission(AviaryGroup):

    def initialize(self):
        super().initialize()
        self.options.declare(
            'subsystems', desc='list of core subsystem builders'
        )
        self.options.declare(
            'meta_data', desc='problem metadata', default=_MetaData
        )
        # NOTE this flag is only needed for tests - in AviaryProblem it should always be False
        self.options.declare('process_overrides', types=bool, default=True,
                             desc='When True, overrides are handled here, otherwise, '
                                  'they are handled in the parent system.')

    def setup(self, **kwargs):
        if use_new_openmdao_syntax:
            # rely on openMDAO's auto-ordering for this group
            self.options['auto_order'] = True

        aviary_options = self.options['aviary_options']
        core_subsystems = self.options['subsystems']

        for subsystem in core_subsystems:
            self.add_subsystem(
                subsystem.name,
                subsystem.build_pre_mission(aviary_options),
                promotes_inputs=['*'],
                promotes_outputs=['*']
            )

    def configure(self):
        super().configure()
        self.manual_overrides = []
        for subsystem in self.options['subsystems']:
            try:
                self.manual_overrides.extend(getattr(getattr(self, subsystem.name),
                                                     'manual_overrides'))
            except:
                continue

        if self.options['process_overrides']:
            override_aviary_vars(self, self.options["aviary_options"],
                                 manual_overrides=self.manual_overrides)
