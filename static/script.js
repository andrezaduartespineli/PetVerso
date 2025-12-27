function mascaraCPF(i) {
        let v = i.value.replace(/\D/g, ""); // Remove tudo o que não é dígito
        if (v.length > 11) v = v.slice(0, 11); // Limita a 11 números
        i.value = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    }

    function mascaraCNPJ(i) {
        let v = i.value.replace(/\D/g, "");
        if (v.length > 14) v = v.slice(0, 14);
        i.value = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
    }

    function mascaraTelefone(i) {
        // 1. Remove tudo que não é número
        let v = i.value.replace(/\D/g, "");
        
        // 2. Limita a 11 dígitos (Celular)
        v = v.slice(0, 11);

        // 3. Aplica a formatação progressiva (evita travar ao apagar)
        if (v.length > 10) {
            // Formato Celular (11 núm): (XX) XXXXX-XXXX
            v = v.replace(/^(\d\d)(\d{5})(\d{4}).*/, "($1) $2-$3");
        } else if (v.length > 5) {
            // Formato Fixo ou digitando (10 núm): (XX) XXXX-XXXX
            v = v.replace(/^(\d\d)(\d{4})(\d{0,4}).*/, "($1) $2-$3");
        } else if (v.length > 2) {
            // Apenas DDD digitado: (XX) 000...
            v = v.replace(/^(\d\d)(\d{0,5})/, "($1) $2");
        } else {
            // Menos de 2 dígitos, não faz nada (deixa apagar o DDD)
            v = v.replace(/^(\d*)/, "$1");
        }

        i.value = v;
    }

    function mascaraCEP(i) {
        let v = i.value.replace(/\D/g, "");
        if (v.length > 8) v = v.slice(0, 8);
        i.value = v.replace(/^(\d{5})(\d{3})/, "$1-$2");
    }