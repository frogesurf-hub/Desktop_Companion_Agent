using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

using DesktopCompanion.Desktop.ApplicationServices;
using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.Presentation;

public sealed class MainWindowViewModel : INotifyPropertyChanged
{
    private readonly IAgentClientService _agentClientService;
    private readonly Uri _endpoint;

    private string _inputText = string.Empty;
    private string _connectionStatus = "Disconnected";

    public MainWindowViewModel(
        IAgentClientService agentClientService,
        Uri endpoint)
    {
        _agentClientService = agentClientService;
        _endpoint = endpoint;

        _agentClientService.MessageReceived +=
            OnMessageReceived;

        _agentClientService.ReceiveFailed +=
            OnReceiveFailed;
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    public ObservableCollection<string> Messages { get; } = [];

    public string InputText
    {
        get => _inputText;

        set
        {
            if (_inputText == value)
            {
                return;
            }

            _inputText = value;
            OnPropertyChanged();
        }
    }

    public string ConnectionStatus
    {
        get => _connectionStatus;

        private set
        {
            if (_connectionStatus == value)
            {
                return;
            }

            _connectionStatus = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(IsConnected));
        }
    }

    public bool IsConnected =>
        _agentClientService.IsConnected;

    public async Task ConnectAsync(
        CancellationToken cancellationToken = default)
    {
        if (_agentClientService.IsConnected)
        {
            return;
        }

        ConnectionStatus = "Connecting...";

        try
        {
            await _agentClientService.ConnectAsync(
                _endpoint,
                cancellationToken);

            ConnectionStatus = "Connected";
        }
        catch
        {
            ConnectionStatus = "Connection failed";
            throw;
        }
    }

    public async Task SendChatAsync(
        CancellationToken cancellationToken = default)
    {
        string message = InputText.Trim();

        if (string.IsNullOrWhiteSpace(message))
        {
            return;
        }

        if (!_agentClientService.IsConnected)
        {
            throw new InvalidOperationException(
                "The Agent Core is not connected.");
        }

        Messages.Add(
            $"You: {message}");

        InputText = string.Empty;

        await _agentClientService.SendChatAsync(
            message,
            cancellationToken);
    }

    public async Task DisconnectAsync(
        CancellationToken cancellationToken = default)
    {
        if (!_agentClientService.IsConnected)
        {
            ConnectionStatus = "Disconnected";
            return;
        }

        await _agentClientService.DisconnectAsync(
            cancellationToken);

        ConnectionStatus = "Disconnected";
    }

    private void OnMessageReceived(
        AgentMessage message)
    {
        _ = System.Windows.Application.Current.Dispatcher.InvokeAsync(
            () =>
            {
                string content =
                    message.Payload["message"]?.ToString()
                    ?? "(empty message)";

                Messages.Add(
                    $"Agent: {content}");
            });
    }

    private void OnReceiveFailed(
        Exception exception)
    {
        _ = System.Windows.Application.Current.Dispatcher.InvokeAsync(
            () =>
            {
                ConnectionStatus = "Connection error";

                Messages.Add(
                    $"System: {exception.Message}");
            });
    }

    private void OnPropertyChanged(
        [CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(
            this,
            new PropertyChangedEventArgs(propertyName));
    }
}
