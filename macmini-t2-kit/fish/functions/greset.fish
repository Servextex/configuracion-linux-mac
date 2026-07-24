# Re-aplica el .gitignore a archivos ya rastreados (los saca del indice sin borrarlos del disco).
function greset
    git rm -r --cached . ; and git add . ; and git commit -m "Ignore Reset" ; and git pull ; and git push
end
