
import Dropdown from 'react-bootstrap/Dropdown'

interface DropdownSelectorProps {
    buttonText?: string;
    variant?: string;
    id: string;
    onSelect?: (eventKey: string | null, event: React.SyntheticEvent<unknown>) => void;
    children: React.ReactNode;
}

function DropdownSelector(props: DropdownSelectorProps) {
    const { buttonText="Dropdown", variant="primary", id, onSelect=undefined} = props;

    return (
        <Dropdown onSelect={onSelect}>
            <Dropdown.Toggle variant={variant} id={id}>
                {buttonText}
            </Dropdown.Toggle>

            <Dropdown.Menu>
                {props.children}
            </Dropdown.Menu>

        </Dropdown>
    );
}

export default DropdownSelector;