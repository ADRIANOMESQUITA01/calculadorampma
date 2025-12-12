from datetime import date, timedelta, datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------- CONFIGURAÇÃO BÁSICA ------------------------- #

st.set_page_config(
    page_title="Calculadora de Datas",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

WEEKDAYS_PT = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]


def formatar_data(d: date) -> str:
    """Formata data como 01/01/2025 (quarta-feira)."""
    dia_semana = WEEKDAYS_PT[d.weekday()]
    return f"{d.strftime('%d/%m/%Y')} ({dia_semana})"


# ---------------------- ESTADO (HISTÓRICO / RESULTADO) ----------------- #

if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = ""


def registrar_calculo(tipo, data_inicial, data_final, qtd_dias, resumo):
    st.session_state["historico"].append(
        {
            "Tipo": tipo,
            "Data inicial": data_inicial.strftime("%d/%m/%Y") if data_inicial else "",
            "Data final": data_final.strftime("%d/%m/%Y") if data_final else "",
            "Qtd dias": qtd_dias,
            "Resumo": resumo,
        }
    )


def botao_copiar(texto: str):
    """Botão copiar para área de transferência."""
    if not texto:
        return

    safe_text = (
        texto.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", "\\n")
    )

    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)"
                style="
                    margin-top:8px;
                    padding:6px 12px;
                    border-radius:6px;
                    border:none;
                    background-color:#4CAF50;
                    color:white;
                    cursor:pointer;
                ">
            📋 Copiar resultado
        </button>
        """,
        height=60,
    )


# ------------- FUNÇÃO PARA DIGITAR DATA COM MÁSCARA dd/mm/aaaa -------- #

def selecionar_data(rotulo: str, valor_padrao: str, chave: str) -> date:
    """
    Campo de texto com máscara automática dd/mm/aaaa.
    Converte o valor final para date e valida.
    """

    texto = st.text_input(
        f"{rotulo} (dd/mm/aaaa)",
        value=valor_padrao,
        key=chave,
        placeholder="dd/mm/aaaa",
    )

    # Máscara JS aplicada ao ÚLTIMO input com esse placeholder
    components.html(
        """
        <script>
        (function() {
            const inputs = window.parent.document.querySelectorAll('input[placeholder="dd/mm/aaaa"]');
            if (!inputs.length) return;
            const campo = inputs[inputs.length - 1];  // último criado
            if (campo.dataset.masked === "true") return; // evita duplicar

            campo.dataset.masked = "true";

            campo.addEventListener('input', function() {
                let v = campo.value.replace(/\\D/g, "").slice(0, 8);
                let f = "";
                if (v.length <= 2) {
                    f = v;
                } else if (v.length <= 4) {
                    f = v.slice(0,2) + "/" + v.slice(2);
                } else {
                    f = v.slice(0,2) + "/" + v.slice(2,4) + "/" + v.slice(4);
                }
                campo.value = f;
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )

    texto = texto.strip()
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        st.error(f"Data inválida no campo **{rotulo}** — digite no formato dd/mm/aaaa.")
        st.stop()


# ------------------------------- SIDEBAR -------------------------------- #

with st.sidebar:
    st.title("🗓️ Calculadora de Datas")
    st.markdown(
        """
        ➤ Digite sempre no formato **dd/mm/aaaa**  

        Tipos de cálculo:
        1. Diferença entre datas  
        2. Data final (início + dias)  
        3. Data inicial (final - dias)  

        Extras:
        - Botão **Copiar resultado**
        - **Histórico** com exportação CSV/Excel
        - Botão **Limpar histórico**
        """
    )

# ----------------------------- CABEÇALHO -------------------------------- #

st.markdown(
    """
    <div style="text-align:center;">
        <h2>🗓️ Calculadora de Datas</h2>
        <p>Campos com máscara automática para <b>dd/mm/aaaa</b>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ----------------------------- MENU OPÇÕES ------------------------------ #

opcao = st.radio(
    "Selecione o tipo de cálculo:",
    [
        "1 - Quantidade de dias entre duas datas",
        "2 - Data final (data inicial + quantidade de dias)",
        "3 - Data inicial (data final - quantidade de dias)",
    ]
)

st.divider()

# ======================================================================
#                         OPÇÃO 1 – DIFERENÇA DE DATAS
# ======================================================================

if opcao.startswith("1"):

    st.subheader("Diferença entre datas")

    modo = st.radio(
        "Modo de contagem:",
        [
            "De data a data (inclui data inicial e final)",
            "Somente dias completos entre as datas",
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        data_inicial = selecionar_data(
            "Data inicial", "01/01/2025", "data_inicial_op1"
        )
    with col2:
        data_final = selecionar_data(
            "Data final", "10/01/2025", "data_final_op1"
        )

    if data_final < data_inicial:
        st.error("A data final não pode ser anterior à inicial.")
        st.stop()

    dias_bruto = (data_final - data_inicial).days

    if modo.startswith("De data a data"):
        dias = dias_bruto + 1
        descricao = "Contagem de data a data (incluindo a data inicial e a data final)"
    else:
        dias = dias_bruto
        descricao = "Somente dias completos entre as datas (exclui a data inicial)"

    st.markdown(f"- **Data inicial:** {formatar_data(data_inicial)}")
    st.markdown(f"- **Data final:** {formatar_data(data_final)}")
    st.markdown(f"- **Modo de contagem:** {descricao}")
    st.success(f"Total: **{dias} dia(s)**")

    resultado = (
        f"Cálculo de diferença entre datas\n"
        f"{descricao}\n"
        f"Data inicial: {formatar_data(data_inicial)}\n"
        f"Data final: {formatar_data(data_final)}\n"
        f"Total de dias: {dias}"
    )

    botao_copiar(resultado)

    registrar_calculo("Diferença entre datas", data_inicial, data_final, dias, descricao)

# ======================================================================
#                     OPÇÃO 2 – DATA FINAL
# ======================================================================

elif opcao.startswith("2"):

    st.subheader("Data final (data inicial + dias)")

    col1, col2 = st.columns(2)

    with col1:
        data_inicial = selecionar_data("Data inicial", "01/01/2025", "data_inicial_op2")

    with col2:
        qtd = st.number_input("Dias a adicionar:", min_value=0, value=9, step=1)

    data_final = data_inicial + timedelta(days=int(qtd))

    st.markdown(f"- **Data inicial:** {formatar_data(data_inicial)}")
    st.markdown(f"- **Dias adicionados:** {int(qtd)}")
    st.success(f"Data final: **{formatar_data(data_final)}**")

    resultado = (
        f"Data final (início + dias)\n"
        f"Data inicial: {formatar_data(data_inicial)}\n"
        f"Dias adicionados: {int(qtd)}\n"
        f"Data final: {formatar_data(data_final)}"
    )

    botao_copiar(resultado)

    registrar_calculo("Data final (início + dias)", data_inicial, data_final, int(qtd), "Somatório")

# ======================================================================
#                     OPÇÃO 3 – DATA INICIAL
# ======================================================================

else:

    st.subheader("Data inicial (data final - dias)")

    col1, col2 = st.columns(2)

    with col1:
        data_final = selecionar_data("Data final", "10/01/2025", "data_final_op3")

    with col2:
        qtd = st.number_input("Dias a subtrair:", min_value=0, value=9, step=1)

    data_inicial = data_final - timedelta(days=int(qtd))

    st.markdown(f"- **Data final:** {formatar_data(data_final)}")
    st.markdown(f"- **Dias subtraídos:** {int(qtd)}")
    st.success(f"Data inicial: **{formatar_data(data_inicial)}**")

    resultado = (
        f"Data inicial (final - dias)\n"
        f"Data final: {formatar_data(data_final)}\n"
        f"Dias subtraídos: {int(qtd)}\n"
        f"Data inicial: {formatar_data(data_inicial)}"
    )

    botao_copiar(resultado)

    registrar_calculo("Data inicial (final - dias)", data_inicial, data_final, int(qtd), "Subtração")

# ======================================================================
#                          HISTÓRICO
# ======================================================================

st.divider()
st.subheader("📜 Histórico")

if st.session_state["historico"]:
    df = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df, use_container_width=True)

    # EXPORTAÇÃO CSV (sempre funciona)
    csv = df.to_csv(index=False).encode("utf-8")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇️ Baixar CSV",
            csv,
            "historico_calculadora_datas.csv",
            mime="text/csv",
        )

    # EXPORTAÇÃO EXCEL (com tratamento de erro)
    with col2:
        try:
            excel = BytesIO()
            df.to_excel(excel, index=False, sheet_name="Histórico")
            excel.seek(0)
            st.download_button(
                "⬇️ Baixar Excel",
                excel,
                "historico_calculadora_datas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ModuleNotFoundError:
            st.warning(
                "Para exportar em Excel (.xlsx), instale o pacote **openpyxl** "
                "no ambiente (requirements.txt)."
            )

    # BOTÃO LIMPAR HISTÓRICO
    with col3:
        if st.button("🧹 Limpar histórico"):
            st.session_state["historico"] = []
            st.success("Histórico limpo!")

else:
    st.info("Nenhum cálculo registrado.")
