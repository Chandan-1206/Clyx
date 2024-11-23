async function submitBrand() {
    const response = await fetch('http://localhost:5000/add-brand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            brand_name: document.getElementById('brand_name').value,
            industry: document.getElementById('industry').value,
            contact_person_name: document.getElementById('contact_person_name').value,
            contact_email: document.getElementById('contact_email').value,
            contact_phone: document.getElementById('contact_phone').value,
            password: document.getElementById('password').value
        }),
    });

    const result = await response.json();
    console.log(result);
}