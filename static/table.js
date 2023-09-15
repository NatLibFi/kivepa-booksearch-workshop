async function populateSelectedBooksTable(labels_set) {
    try {
        const response = await fetch('/' + labels_set + '/get_selected_books');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();

        const tableBody = $('#selected-books-table-' + labels_set + ' tbody');

        let rowNumber = 1; // Initialize the row number

        console.log(data.selectedBooks.length);
        data.selectedBooks.forEach(book => {
            console.log(book);
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
