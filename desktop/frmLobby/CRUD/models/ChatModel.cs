using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowLobby.CRUD.models
{
    public class ChatModel
    {
        public int id_chat { get; set; }

        public int id_grupo { get; set; }

        public int id_usuario { get; set; }

        public string pergunta { get; set; }

        public string resposta { get; set; }

        public string data_interacao { get; set; }
    }
}
