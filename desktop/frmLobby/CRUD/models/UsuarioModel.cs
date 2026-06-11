using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowLobby.CRUD.models
{
    public class UsuarioModel
    {
        public int id_usuario { get; set; }

        public string nome { get; set; }

        public string email { get; set; }

        public string? data_criacao { get; set; }

        public string? foto_perfil { get; set; }
    }
}
