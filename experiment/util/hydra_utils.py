#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2021 Nathan Juraj Michlo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

import logging

from deprecated import deprecated
from omegaconf import DictConfig
from omegaconf import OmegaConf


log = logging.getLogger(__name__)


# ========================================================================= #
# Better Specializations                                                    #
# TODO: this might be replaced by recursive instantiation                   #
#       https://github.com/facebookresearch/hydra/pull/1044                 #
# ========================================================================= #


@deprecated('replace with hydra 1.1')
def make_non_strict(cfg: DictConfig):
    return OmegaConf.create({**cfg})


@deprecated('replace with hydra 1.1')
def merge_specializations(cfg: DictConfig, config_path: str, main_fn: callable, strict=True):
    # TODO: this should eventually be replaced with hydra recursive defaults
    # TODO: this makes config non-strict, allows setdefault to work even if key does not exist in config

    # skip if we do not have any specializations
    if 'specializations' not in cfg:
        return

    if not strict:
        # we allow overwrites & missing values to be inserted
        cfg = make_non_strict(cfg)

    # imports
    import os
    from hydra._internal.utils import detect_calling_file_or_module_from_task_function

    # get hydra config root
    calling_file, _, _ = detect_calling_file_or_module_from_task_function(main_fn)
    config_root = os.path.join(os.path.dirname(calling_file), config_path)

    # set and update specializations
    for group, specialization in cfg.specializations.items():
        assert group not in cfg, f'group={repr(group)} already exists on cfg, specialization merging is not supported!'
        log.info(f'merging specialization: {repr(specialization)}')
        # load specialization config
        specialization_cfg = OmegaConf.load(os.path.join(config_root, group, f'{specialization}.yaml'))
        # create new config
        cfg = OmegaConf.merge(cfg, {group: specialization_cfg})

    # remove specializations key
    del cfg['specializations']

    # done
    return cfg


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
