param(
    [string]$HtmlPath = "submission/evidence/11-dashboard-overview.html",
    [string]$OutputPath = "submission/evidence/11-dashboard-overview.png"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$html = Get-Content -Raw -Encoding UTF8 -LiteralPath $HtmlPath
$panelMatches = [regex]::Matches(
    $html,
    '<article class="panel">(.*?)</article>',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if ($panelMatches.Count -ne 6) {
    throw "Expected six dashboard panels, found $($panelMatches.Count)."
}

$bitmap = New-Object System.Drawing.Bitmap 1200, 760
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

$background = [System.Drawing.ColorTranslator]::FromHtml("#08111f")
$panelColor = [System.Drawing.ColorTranslator]::FromHtml("#0f1c2e")
$borderColor = [System.Drawing.ColorTranslator]::FromHtml("#223652")
$textColor = [System.Drawing.ColorTranslator]::FromHtml("#e6edf7")
$mutedColor = [System.Drawing.ColorTranslator]::FromHtml("#91a2ba")
$trackColor = [System.Drawing.ColorTranslator]::FromHtml("#24344a")
$healthyColor = [System.Drawing.ColorTranslator]::FromHtml("#37c99b")
$breachColor = [System.Drawing.ColorTranslator]::FromHtml("#ff6b6b")

$backgroundBrush = New-Object System.Drawing.SolidBrush $background
$panelBrush = New-Object System.Drawing.SolidBrush $panelColor
$textBrush = New-Object System.Drawing.SolidBrush $textColor
$mutedBrush = New-Object System.Drawing.SolidBrush $mutedColor
$trackBrush = New-Object System.Drawing.SolidBrush $trackColor
$healthyBrush = New-Object System.Drawing.SolidBrush $healthyColor
$breachBrush = New-Object System.Drawing.SolidBrush $breachColor
$borderPen = New-Object System.Drawing.Pen $borderColor, 1

$titleFont = New-Object System.Drawing.Font "Segoe UI", 24, ([System.Drawing.FontStyle]::Bold)
$subtitleFont = New-Object System.Drawing.Font "Segoe UI", 11
$panelTitleFont = New-Object System.Drawing.Font "Segoe UI", 12
$valueFont = New-Object System.Drawing.Font "Segoe UI", 25, ([System.Drawing.FontStyle]::Bold)
$detailFont = New-Object System.Drawing.Font "Segoe UI", 10

try {
    $graphics.Clear($background)
    $graphics.DrawString("Monitoring & LLMOps", $titleFont, $textBrush, 40, 28)
    $graphics.DrawString("Metrics -> Logs -> Traces | 60-minute operational view", $subtitleFont, $mutedBrush, 42, 72)

    for ($index = 0; $index -lt $panelMatches.Count; $index++) {
        $panel = $panelMatches[$index].Groups[1].Value
        $column = $index % 3
        $row = [math]::Floor($index / 3)
        $x = 40 + ($column * 385)
        $y = 120 + ($row * 295)

        $title = [System.Net.WebUtility]::HtmlDecode([regex]::Match($panel, '<h2>(.*?)</h2>').Groups[1].Value)
        $valueMatch = [regex]::Match($panel, '<div class="value">(.*?)<span class="unit">(.*?)</span>')
        $value = [System.Net.WebUtility]::HtmlDecode(($valueMatch.Groups[1].Value -replace '<[^>]+>', ''))
        $unit = [System.Net.WebUtility]::HtmlDecode($valueMatch.Groups[2].Value)
        $threshold = [System.Net.WebUtility]::HtmlDecode([regex]::Match($panel, '<div class="threshold-label">(.*?)</div>').Groups[1].Value)
        $fillPercent = [double]([regex]::Match($panel, 'class="fill (?:healthy|breach)" style="width:([\d.]+)%"').Groups[1].Value)
        $fillWidth = [math]::Round(300 * $fillPercent / 100)
        $fillBrush = if ($panel -match 'class="fill breach"') { $breachBrush } else { $healthyBrush }

        $graphics.FillRectangle($panelBrush, $x, $y, 345, 255)
        $graphics.DrawRectangle($borderPen, $x, $y, 345, 255)
        $graphics.DrawString($title, $panelTitleFont, $mutedBrush, $x + 22, $y + 20)
        $graphics.DrawString($value, $valueFont, $textBrush, $x + 22, $y + 57)
        $graphics.DrawString($unit, $detailFont, $mutedBrush, $x + 22, $y + 107)
        $graphics.FillRectangle($trackBrush, $x + 22, $y + 135, 300, 8)
        if ($fillWidth -gt 0) {
            $graphics.FillRectangle($fillBrush, $x + 22, $y + 135, $fillWidth, 8)
        }
        $graphics.DrawString($threshold, $detailFont, $mutedBrush, $x + 22, $y + 154)

        $facts = [regex]::Matches($panel, '<span>(.*?)<strong>(.*?)</strong></span>')
        for ($factIndex = 0; $factIndex -lt [math]::Min(4, $facts.Count); $factIndex++) {
            $factX = $x + 22 + (($factIndex % 2) * 160)
            $factY = $y + 190 + ([math]::Floor($factIndex / 2) * 28)
            $label = [System.Net.WebUtility]::HtmlDecode($facts[$factIndex].Groups[1].Value)
            $factValue = [System.Net.WebUtility]::HtmlDecode($facts[$factIndex].Groups[2].Value)
            $graphics.DrawString("$label`: $factValue", $detailFont, $textBrush, $factX, $factY)
        }
    }

    $graphics.DrawString("Source: data/logs.jsonl | Aggregate metrics only | No raw prompt or PII", $detailFont, $mutedBrush, 42, 725)
    $outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = [System.IO.Path]::GetDirectoryName($outputFullPath)
    [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    $bitmap.Save($outputFullPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "Dashboard PNG written to $outputFullPath"
}
finally {
    $graphics.Dispose()
    $bitmap.Dispose()
    $backgroundBrush.Dispose()
    $panelBrush.Dispose()
    $textBrush.Dispose()
    $mutedBrush.Dispose()
    $trackBrush.Dispose()
    $healthyBrush.Dispose()
    $breachBrush.Dispose()
    $borderPen.Dispose()
    $titleFont.Dispose()
    $subtitleFont.Dispose()
    $panelTitleFont.Dispose()
    $valueFont.Dispose()
    $detailFont.Dispose()
}
