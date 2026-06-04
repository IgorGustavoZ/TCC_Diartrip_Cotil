using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowLobby.CRUD.models
{
    class ViagemModel
    {
        public int id_grupo { get; set; }

        public string nome_grupo { get; set; }

        public string destino_principal { get; set; }

        public string data_inicio { get; set; }

        public string data_fim { get; set; }

        public string codigo_convite { get; set; }

        public string criador { get; set; }

    }
}
