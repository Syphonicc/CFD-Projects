#!/bin/bash
# ---------------------------------------------------------------------------
# N2A post-processing: Cp at four spanwise stations, Mach maxima, separation
#
# Runs OpenFOAM utilities only - no ParaView, no GUI, low memory.
#
# Spanwise stations from Aprovitola et al., as fractions of semi-span.
# Semi-span = 1.88275 m:
#     13.4%  ->  y = 0.25229
#     30.5%  ->  y = 0.57424
#     51.0%  ->  y = 0.96020
#     90.6%  ->  y = 1.70577
#
# Usage:
#     ./extract.sh                    # all four cases
#     ./extract.sh a10_SA             # one case
# ---------------------------------------------------------------------------
set -u

RESULTS=~/CFD-Projects/n2a-validation/results
OUT=~/CFD-Projects/n2a-validation/analysis

# freestream, for Cp normalisation
P_INF=93290.0
RHO_INF=1.1281
U_INF=68.05
Q_INF=$(python3 -c "print(0.5*$RHO_INF*$U_INF**2)")

STATIONS="0.25229 0.57424 0.96020 1.70577"
LABELS="13.4 30.5 51.0 90.6"

CASES=${1:-"a6_SA a6_SST a10_SA a10_SST"}

echo "q_inf = $Q_INF Pa"
mkdir -p "$OUT"

for c in $CASES; do
    CASE="$RESULTS/$c/OPENFOAM-solution"
    if [ ! -d "$CASE" ]; then
        echo "!! $c not found at $CASE"
        continue
    fi

    LATEST=$(ls -d "$CASE"/[0-9]* 2>/dev/null | grep -v '/0$' | sort -n | tail -1)
    T=$(basename "$LATEST")
    echo ""
    echo "==================================================="
    echo "$c   latest time = $T"
    echo "==================================================="

    # ---- write a sampling dict for this case -------------------------------
    mkdir -p "$CASE/system"
    {
        echo 'FoamFile { version 2.0; format ascii; class dictionary; object sampleDict; }'
        echo ''
        echo 'type            surfaces;'
        echo 'libs            (sampling);'
        echo 'interpolationScheme cellPoint;'
        echo 'surfaceFormat   raw;'
        echo 'fields          (p U Ma wallShearStress yPlus);'
        echo ''
        echo 'surfaces'
        echo '{'
        i=1
        for y in $STATIONS; do
            echo "    station$i"
            echo '    {'
            echo '        type            cuttingPlane;'
            echo '        planeType       pointAndNormal;'
            echo '        pointAndNormalDict'
            echo '        {'
            echo "            point   (0 $y 0);"
            echo '            normal  (0 1 0);'
            echo '        }'
            echo '        interpolate     true;'
            echo '    }'
            i=$((i+1))
        done
        echo ''
        echo '    aircraft'
        echo '    {'
        echo '        type            patch;'
        echo '        patches         (n2a);'
        echo '        interpolate     false;'
        echo '    }'
        echo '}'
    } > "$CASE/system/sampleDict"

    cd "$CASE" || continue

    echo "-- sampling surfaces ..."
    postProcess -func sampleDict -time "$T" > log.sample 2>&1
    tail -3 log.sample

    echo "-- field extrema ..."
    postProcess -func "components(U)" -time "$T" > /dev/null 2>&1

    # Mach maxima
    echo "-- Mach number ..."
    postProcess -func "volFieldValue(fields=(Ma),operation=max)" -time "$T" > log.MaMax 2>&1
    grep -iE "max\(Ma\)" log.MaMax | tail -2

    # wall shear stress extrema on the aircraft
    echo "-- wall shear stress on n2a ..."
    postProcess -func "patchIntegrate(patch=n2a,field=wallShearStress)" -time "$T" > log.wss 2>&1
    tail -3 log.wss

    mkdir -p "$OUT/$c"
    if [ -d "postProcessing/sampleDict/$T" ]; then
        cp -r "postProcessing/sampleDict/$T"/* "$OUT/$c/" 2>/dev/null
        echo "-- copied samples to $OUT/$c"
        ls "$OUT/$c" | head
    else
        echo "!! no sample output found - check log.sample"
    fi
done

echo ""
echo "Done. Samples in $OUT"
