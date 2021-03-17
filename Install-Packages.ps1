# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

$wheels = Get-ChildItem("wheels")
$python = Get-Item("venv\Scripts\python.exe")
$requirements = Get-Item("requirements.txt")

# Install custom wheels, binding, etc.
foreach ($item in $wheels) {
    Invoke-Expression "$python -m pip install $item"
}

# Install other requirements
foreach($line in Get-Content $requirements) {
    Invoke-Expression "$python -m pip install $line"
}
