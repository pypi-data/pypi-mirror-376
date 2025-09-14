import subprocess

# Script PowerShell como string
ps_script = r'''
Add-Type -AssemblyName PresentationFramework

# Observable para conexiones TCP
$observable = New-Object System.Collections.ObjectModel.ObservableCollection[object]

# Observable para archivos pesados
$filesObservable = New-Object System.Collections.ObjectModel.ObservableCollection[object]

# XAML con TabControl
[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="SysOps" Height="650" Width="1100"
        WindowStartupLocation="CenterScreen" Background="White" FontFamily="Segoe UI">

    <TabControl>
        <TabItem Header="Conexiones TCP">
            <Grid Margin="10">
                <Grid.RowDefinitions>
                    <RowDefinition Height="40"/>
                    <RowDefinition Height="*"/>
                    <RowDefinition Height="40"/>
                </Grid.RowDefinitions>

                <StackPanel Grid.Row="0" Orientation="Horizontal" VerticalAlignment="Center">
                    <TextBlock Text="Filtrar por estado:" VerticalAlignment="Center" Margin="0,0,10,0" FontWeight="Bold"/>
                    <ComboBox x:Name="FilterBox" Width="200" SelectedIndex="0">
                        <ComboBoxItem Content="Todos"/>
                        <ComboBoxItem Content="Established"/>
                        <ComboBoxItem Content="Listen"/>
                        <ComboBoxItem Content="Bound"/>
                        <ComboBoxItem Content="TimeWait"/>
                        <ComboBoxItem Content="CloseWait"/>
                    </ComboBox>
                    <Button x:Name="RefreshBtn" Content="Actualizar" Width="120" Margin="20,0,0,0"
                            Background="#4CAF50" Foreground="White" FontWeight="Bold"/>
                </StackPanel>

                <DataGrid x:Name="ConnGrid" Grid.Row="1"
                          IsReadOnly="True"
                          AutoGenerateColumns="False"
                          AlternatingRowBackground="#F0F0F0"
                          HeadersVisibility="Column"
                          GridLinesVisibility="None"
                          SelectionMode="Single"
                          SelectionUnit="FullRow"
                          Margin="0,5,0,10"
                          FontSize="13"
                          ItemsSource="{Binding}">
                    <DataGrid.Columns>
                        <DataGridTextColumn Header="Local" Binding="{Binding Local}" Width="200"/>
                        <DataGridTextColumn Header="Remote" Binding="{Binding Remote}" Width="200"/>
                        <DataGridTextColumn Header="State" Binding="{Binding State}" Width="100"/>
                        <DataGridTextColumn Header="PID" Binding="{Binding PID}" Width="70"/>
                        <DataGridTextColumn Header="Proceso" Binding="{Binding Process}" Width="150"/>
                        <DataGridTextColumn Header="Ruta" Binding="{Binding Path}" Width="*"/>
                    </DataGrid.Columns>
                </DataGrid>

                <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button x:Name="KillBtn" Content="Matar Proceso" Width="120"
                            Background="#D32F2F" Foreground="White" FontWeight="Bold"/>
                </StackPanel>
            </Grid>
        </TabItem>

        <TabItem Header="Archivos Pesados">
            <Grid Margin="10">
                <Grid.RowDefinitions>
                    <RowDefinition Height="40"/>
                    <RowDefinition Height="*"/>
                    <RowDefinition Height="40"/>
                </Grid.RowDefinitions>

                <StackPanel Grid.Row="0" Orientation="Horizontal" VerticalAlignment="Center">
                    <TextBlock Text="Escaneo de archivos grandes en el perfil de usuario"
                               VerticalAlignment="Center" FontWeight="Bold" Margin="0,0,20,0"/>
                    <Button x:Name="ScanBtn" Content="Escanear"
                            Width="120" Background="#1976D2" Foreground="White" FontWeight="Bold"/>
                </StackPanel>

                <DataGrid x:Name="FilesGrid" Grid.Row="1"
                          IsReadOnly="True"
                          AutoGenerateColumns="False"
                          AlternatingRowBackground="#F0F0F0"
                          HeadersVisibility="Column"
                          GridLinesVisibility="None"
                          SelectionMode="Single"
                          SelectionUnit="FullRow"
                          Margin="0,5,0,10"
                          FontSize="13"
                          ItemsSource="{Binding}">
                    <DataGrid.Columns>
                        <DataGridTextColumn Header="Archivo" Binding="{Binding FullName}" Width="*"/>
                        <DataGridTextColumn Header="Tamaño (GB)" Binding="{Binding Size}" Width="150"/>
                    </DataGrid.Columns>
                </DataGrid>

                <TextBlock x:Name="StatusLbl" Grid.Row="2" Text="Listo."
                           VerticalAlignment="Center" HorizontalAlignment="Left" FontStyle="Italic"/>
            </Grid>
        </TabItem>
    </TabControl>
</Window>
"@

# Cargar XAML
$reader = (New-Object System.Xml.XmlNodeReader $xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)

# Controles
$connGrid   = $window.FindName("ConnGrid")
$killBtn    = $window.FindName("KillBtn")
$filterBox  = $window.FindName("FilterBox")
$refreshBtn = $window.FindName("RefreshBtn")
$scanBtn    = $window.FindName("ScanBtn")
$filesGrid  = $window.FindName("FilesGrid")
$statusLbl  = $window.FindName("StatusLbl")

$connGrid.ItemsSource  = $observable
$filesGrid.ItemsSource = $filesObservable

function Load-Connections {
    param($filter)
    $conns = Get-NetTCPConnection | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            Local   = "$($_.LocalAddress):$($_.LocalPort)"
            Remote  = "$($_.RemoteAddress):$($_.RemotePort)"
            State   = $_.State
            PID     = $_.OwningProcess
            Process = $proc.ProcessName
            Path    = $proc.Path
        }
    }
    if ($filter -and $filter -ne "Todos") {
        $conns = $conns | Where-Object { $_.State -eq $filter }
    }
    return ,$conns
}

function Refresh-Connections {
    $selected = $filterBox.SelectedItem.Content.ToString()
    $newData = Load-Connections $selected
    $observable.Clear()
    foreach ($item in $newData) { $observable.Add($item) }
}

Refresh-Connections
$filterBox.Add_SelectionChanged({ Refresh-Connections })
$refreshBtn.Add_Click({ Refresh-Connections })
$currentPID = $PID

$killBtn.Add_Click({
    if ($connGrid.SelectedItem) {
        $targetPID = [int]$connGrid.SelectedItem.PID
        if ($targetPID -eq $currentPID) {
            [System.Windows.MessageBox]::Show("No puedes matar el proceso de la GUI ($targetPID).")
            return
        }
        try {
            Stop-Process -Id $targetPID -Force
            [System.Windows.MessageBox]::Show("Proceso $targetPID terminado.")
            Refresh-Connections
        } catch {
            [System.Windows.MessageBox]::Show("Error al matar el proceso: $($_.Exception.Message)")
        }
    }
})

$scanBtn.Add_Click({
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $form = New-Object Windows.Forms.Form
    $form.Text = "Cargando..."
    $form.Width = 350
    $form.Height = 120
    $form.StartPosition = "CenterScreen"
    $label = New-Object Windows.Forms.Label
    $label.Text = "Buscando archivos pesados, espera un momento..."
    $label.AutoSize = $true
    $label.Location = New-Object Drawing.Point(20,40)
    $form.Controls.Add($label)
    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()

    $filesObservable.Clear()
    $muestra = 50
    $resultado = Get-ChildItem "$env:USERPROFILE" -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending |
        Select-Object -First $muestra FullName, @{Name="Size";Expression={[math]::Round($_.Length/1GB,2)}}

    foreach ($f in $resultado) {
        $filesObservable.Add($f)
    }

    $form.Close()
    $statusLbl.Text = "Escaneo completado. Se muestran $muestra archivos más pesados."
})

$window.ShowDialog() | Out-Null
'''

subprocess.run([
    "powershell.exe",
    "-ExecutionPolicy", "Bypass",
    "-Command", ps_script
])
