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
