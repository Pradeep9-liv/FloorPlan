# Run from the project root:  powershell -File fixloop\regenerate.ps1
$cap = "data\single_scan_with_ceiling"

function Run-Config($name, $method, $agg, $steps) {
    $env:DIMS_METHOD = $method
    $env:DIMS_AGG = $agg
    python src/repeat.py $cap $steps *> "fixloop\regen_$name.txt"
    Select-String -Path "fixloop\regen_$name.txt" -Pattern "room dimensions within" |
        ForEach-Object { "$name : " + $_.Line }
}

Run-Config "v0_bbox_320frames"     "bbox"  "median"  @("30","31","37")
Run-Config "v1_rays_320frames"     "rays"  "median"  @("30","31","37")
Run-Config "v1_rays_900frames"     "rays"  "median"  @("10","11","13")
Run-Config "v2_cluster_900frames"  "rays"  "cluster" @("10","11","13")

Remove-Item Env:DIMS_METHOD
Remove-Item Env:DIMS_AGG