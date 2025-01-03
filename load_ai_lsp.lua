local client = nil

vim.api.nvim_create_autocmd('FileType', {
    pattern = { 'text' },
    callback = function()
        vim.notify('Attaching overkill-lsp to txt')

        if not client then
            client = vim.lsp.start_client({
                name = 'overkill-lsp',
                cmd = { '/home/igor/work/lsp/runlsp.sh' }
            })
        end

        if not client then
            vim.notify('Failed to start overkill-lsp')
            return
        end

        vim.lsp.buf_attach_client(0, client)
    end
})
