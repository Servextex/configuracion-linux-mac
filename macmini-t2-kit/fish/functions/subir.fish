# Sin argumentos: solo baja cambios.  Con argumentos: usa todo lo escrito como mensaje de commit.
#   subir                 -> git pull
#   subir arregle el bug  -> add . + commit -m "arregle el bug" + pull + push
function subir
    if test (count $argv) -eq 0
        git pull
    else
        git add . ; and git commit -m "$argv" ; and git pull ; and git push
    end
end
