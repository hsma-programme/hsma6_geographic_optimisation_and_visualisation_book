library(glossary)

glossary_setup <- function() {
    glossary_path("glossary.yml")
    glossary_popup("hover")
}

glossary_setup_style <- function() {

    glossary_style(color = "#8A1E1E",
                   text_decoration = "underline",
                   def_bg = "#333",
                   def_color = "white")

}
