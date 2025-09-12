# SPDX-FileCopyrightText: 2025-present Francesco Ballardin <francesco.ballardin@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-only

from . import __about__

__version__ = __about__.__version__
__author__ = __about__.__author__


from . import client

Client = client.Client
