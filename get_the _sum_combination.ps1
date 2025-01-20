function Find-Combinations {
    param (
        [float[]]$numbers,
        [float]$targetSum,
        [float[]]$currentCombo = @(),
        [int]$startIndex = 0
    )

    $currentSum = ($currentCombo | Measure-Object -Sum).Sum
    if ($currentSum -eq $targetSum) {
        ($currentCombo -join ', ')
        return ,@($currentCombo) | Out-Null
    }
    elseif ($currentSum -gt $targetSum) {
        return @() | Out-Null
    }

    for ($i = $startIndex; $i -lt $numbers.Length; $i++) {
         if ($numbers[$i] -ne 0) {
             Find-Combinations -numbers $numbers -targetSum $targetSum -currentCombo ($currentCombo + $numbers[$i]) -startIndex ($i + 1)
         }
    }
}

function Find-Combinations-Stack {
    param (
        [float[]]$numbers,
        [float]$targetSum
    )

    $combinations = @()
    $stack = @([ordered]@{ combination = @(); index = 0 })

    while ($stack.Count -gt 0) {
        $currentCombo = $stack[-1]
        $stack = $stack[0..($stack.Count - 2)]  # Pop the last element from the stack

        $currentSum = ($currentCombo | Measure-Object -Sum).Sum

        if ($currentSum -eq $targetSum) {
            ($currentCombo -join ', ')
            $combinations += ,@($currentCombo)
        }
        elseif ($currentSum -lt $targetSum) {
            $startIndex = 0
            if ($currentCombo.Count -gt 0) {
                $startIndex = [Array]::IndexOf($numbers, $currentCombo[-1]) + 1
            }
            for ($i = $startIndex; $i -lt $numbers.Length; $i++) {
                $stack += @($currentCombo + $numbers[$i])
            }
        }
    }

    return $combinations
}

# Example usage:
#$numbers = @(
#    1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7
#)
#$targetSum = 15.4

#Find-Combinations -numbers $numbers -targetSum $targetSum

# Input prompt for the list of numbers and target sum
$numbers = @()
while ($true) {
    $line = Read-Host "Enter a line of numbers separated by  semicolons (or press Enter to finish)"
    if ($line -eq "") {
        break
    }
    $numbers += $line -replace ",", ""  -split ";" | ForEach-Object { [float]$_ }
}

$targetSum = [float](Read-Host "Enter the target sum")
$sortedNumbers = $numbers | Sort-Object

Find-Combinations -numbers $sortedNumbers -targetSum $targetSum

#Find-Combinations-Stack -numbers $sortedNumbers -targetSum $targetSum

pause