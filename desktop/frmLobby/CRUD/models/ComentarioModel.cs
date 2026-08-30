using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowLobby.CRUD.models
{
    public class ComentarioModel
    {
        public int id { get; set; }

        public int id_post { get; set; }

        public int id_usuario { get; set; }

        public string conteudo { get; set; }

        public string? data_criacao { get; set; }
    }
}
