Add-Type -Path ".\itextsharp.dll"
function print_info {
    param ($path)

    $pdf_o = New-Object iTextSharp.text.pdf.PdfReader -ArgumentList $path.FullName
    
    Write-Output ($path.FullName + ": " + $pdf_o.NumberOfPages + " Pages")

    $pdf_o.dispose() 
}


Get-Item *.pdf | ForEach-Object {print_info($_)}
Get-ChildItem -Dir | Get-ChildItem -R -I *.pdf | ForEach-Object {print_info($_)}
Pause
