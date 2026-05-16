return {
  {
    "Saghen/blink.cmp",
    opts = {
      sources = {
        default = { "snippets", "lsp", "path", "buffer" },
        per_filetype = {
          markdown = { "snippets", "lsp", "path" },
          mdx = { "snippets", "lsp", "path" },
        },
      },
    },
  },
}
