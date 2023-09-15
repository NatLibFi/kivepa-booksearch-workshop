async function populateSelectedBooksTable(labels_set) {
    await $(".selected-books-table").load('/static/table.html');

    try {
        const response = await fetch('/' + labels_set + '/get_selected_books');
        const data = await response.json();

        const tableBody = $('#selected-books-table-' + labels_set + ' tbody');
        tableBody.empty(); // Clear existing rows

        let rowNumber = 1; // Initialize the row number

        data.selectedBooks.forEach(book => {
            const row = $('<tr>');
            row.html(`
                <td>${rowNumber}</td>
                <td>${book.title}</td>
                <td>${book.authors}</td>
                <td>${book.is_found}</td>
            `);
            tableBody.append(row);

            rowNumber++; // Increment the row number for the next row
        });
    } catch (error) {
        console.error('Error fetching selected books:', error);
    }
}
