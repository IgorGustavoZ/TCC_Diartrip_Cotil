using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowLobby.CRUD.models
{
    public class PostModel
    {
        public int id_post { get; set; }

        public string conteudo { get; set; }

        public string imagem { get; set; }

        public string? data_criacao { get; set; }

        public int id_usuario { get; set; }

        public string nome { get; set; }

        public string foto_perfil { get; set; }

        public int curtidas { get; set; }

        //public bool ja_curtiu { get; set; }

        public List<ComentarioModel>? comentarios { get; set; }
    }
}
