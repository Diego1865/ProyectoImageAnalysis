param([string]$InputPath, [string]$PdfPath, [string]$DocPath = '')
$ErrorActionPreference = 'Stop'
$InputPath = [IO.Path]::GetFullPath($InputPath)
$PdfPath = [IO.Path]::GetFullPath($PdfPath)
if ($DocPath) { $DocPath = [IO.Path]::GetFullPath($DocPath) }
$word = $null
$document = $null
try {
    Write-Output 'Starting Word'
    $word = New-Object -ComObject Word.Application
    Write-Output 'Word object created'
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    Write-Output 'Opening document'
    $document = $word.Documents.Open($InputPath, $false, $true)
    Write-Output 'Document opened'
    if ($DocPath) {
        Write-Output 'Saving DOC'
        $document.SaveAs2($DocPath, 0)
        Write-Output 'DOC saved'
    }
    $word.ActivePrinter = 'Microsoft Print to PDF'
    Write-Output 'Exporting PDF'
    $document.ExportAsFixedFormat($PdfPath, 17)
    Write-Output 'PDF exported'
    Write-Output ('Pages: ' + $document.ComputeStatistics(2))
} finally {
    if ($document) { $document.Close(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    if ($word) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
}
