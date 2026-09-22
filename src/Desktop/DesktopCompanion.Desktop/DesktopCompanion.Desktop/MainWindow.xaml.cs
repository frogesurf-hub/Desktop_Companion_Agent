using System.Windows;

using DesktopCompanion.Desktop.Presentation;

namespace DesktopCompanion.Desktop;

public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow(
        MainWindowViewModel viewModel)
    {
        InitializeComponent();

        _viewModel = viewModel;

        DataContext = viewModel;
    }

    private async void ConnectButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            await _viewModel.ConnectAsync();
        }
        catch (Exception exception)
        {
            MessageBox.Show(
                exception.Message,
                "Connection Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private async void SendButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        try
        {
            await _viewModel.SendChatAsync();
        }
        catch (Exception exception)
        {
            MessageBox.Show(
                exception.Message,
                "Send Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private async void RefreshMemoryButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        await _viewModel.Memory.LoadAsync();
    }


    private async void MemoryList_SelectionChanged(
        object sender,
        System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (_viewModel.Memory.SelectedMemory is null)
        {
            return;
        }

        await _viewModel.Memory.InspectSelectedAsync();
    }


    private async void SaveMemoryButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        await _viewModel.Memory.SaveAsync();
    }


    private async void DeleteMemoryButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_viewModel.Memory.SelectedMemory is null)
        {
            return;
        }

        MessageBoxResult result =
            MessageBox.Show(
                "Delete this Memory?",
                "Delete Memory",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning);

        if (result != MessageBoxResult.Yes)
        {
            return;
        }

        await _viewModel.Memory.DeleteAsync();
    }


    private async void HistoryMemoryButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        await _viewModel.Memory.LoadHistoryAsync();
    }


    private void CloseHistoryButton_Click(
        object sender,
        RoutedEventArgs e)
    {
        _viewModel.Memory.HideHistory();
    }

    protected override async void OnClosed(
        EventArgs e)
    {
        base.OnClosed(e);

        try
        {
            await _viewModel.DisconnectAsync();
        }
        catch
        {
            // Window is already closing.
        }
    }
}
