// التعامل مع الحقول بناءً على نوع التسجيل
document.getElementById('type').addEventListener('change', function() {
    var type = this.value;
    
    document.getElementById('individual-fields').classList.add('hidden');
    document.getElementById('academy-fields').classList.add('hidden');
    document.getElementById('university-fields').classList.add('hidden');

    if (type === 'individual') {
        document.getElementById('individual-fields').classList.remove('hidden');
    } else if (type === 'academy') {
        document.getElementById('academy-fields').classList.remove('hidden');
    } else if (type === 'university') {
        document.getElementById('university-fields').classList.remove('hidden');
    }
});
