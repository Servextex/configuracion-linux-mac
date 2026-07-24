source /usr/share/cachyos-fish-config/cachyos-config.fish

# overwrite greeting
# desactivar fastfetch al abrir la terminal (funcion vacia = sin saludo).
# Se sobrescribe AQUI, despues del source de cachyos, para no tocar el archivo del sistema
# /usr/share/cachyos-fish-config/cachyos-config.fish (asi sobrevive a las actualizaciones).
# Para revertir: borrar esta funcion, o poner "fastfetch" dentro.
function fish_greeting
end
export PATH="$HOME/.local/bin:$PATH"
