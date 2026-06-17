using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using WindowLobby.crud;
namespace WindowLogin
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class Login : Window
    {
        public Login()
        {
            InitializeComponent();
        }

        private void btnEntrar_Click(object sender, RoutedEventArgs e)
        {
            // ATENÇÃO: Este projeto (frmLogin) NÃO chama a API de autenticação.
            // Usar o projeto frmLobby como ponto de entrada — contém o login real
            // em frmLobby/Login.xaml.cs que chama Usuario.Login() e valida credenciais.
            Dashboard lobby = new Dashboard();
            lobby.Show();
            this.Close();
        }
    }
}